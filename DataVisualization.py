import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc

url = 'https://en.wikipedia.org/wiki/List_of_FIFA_World_Cup_finals'
tables = pd.read_html(url)

for i, table in enumerate(tables):
    if 'Team' in str(table.columns) and 'Winners' in str(table.columns):
        wcWinnerData = table.copy()
        break

wcWinnerData.columns = ['Team', 'Wins', 'Runners-up', 'Total_finals', 'Years_won', 'Years_runners_up']
wcWinnerData = wcWinnerData.dropna(subset=['Team'])

wcWinnerData['Team'] = (
    wcWinnerData['Team']
    .str.replace(r'\[.*\]', '', regex=True)
    .str.strip()
    .replace({'West Germany': 'Germany'})
)

wcWinnerData['Wins'] = wcWinnerData['Wins'].astype(int)
wcWinnerData['Runners-up'] = wcWinnerData['Runners-up'].astype(int)
wcWinnerData['Total_finals'] = wcWinnerData['Total_finals'].astype(int)

matches = []
for _, row in wcWinnerData.iterrows():
    if pd.notna(row['Years_won']) and row['Years_won'] != '—':
        years = [int(y.strip()) for y in row['Years_won'].split(',')]
        for year in years:
            matches.append({'Year': year, 'Winner': row['Team']})
    
    if pd.notna(row['Years_runners_up']) and row['Years_runners_up'] != '—':
        years = [int(y.strip()) for y in row['Years_runners_up'].split(',')]
        for year in years:
            matches.append({'Year': year, 'Runner-up': row['Team']})

matches_df = pd.DataFrame(matches)
winners = matches_df[matches_df['Winner'].notna()][['Year', 'Winner']]
runners = matches_df[matches_df['Runner-up'].notna()][['Year', 'Runner-up']]
finals_df = winners.merge(runners, on='Year', how='left').drop_duplicates()

app = Dash(__name__)

iso_codes = {
    'Brazil': 'BRA', 'Germany': 'DEU', 'Italy': 'ITA', 'Argentina': 'ARG',
    'France': 'FRA', 'Uruguay': 'URY', 'England': 'GBR', 'Spain': 'ESP',
    'Netherlands': 'NLD', 'Hungary': 'HUN', 'Czechoslovakia': 'CZE',
    'Sweden': 'SWE', 'Croatia': 'HRV'
}

wcWinnerData['Code'] = wcWinnerData['Team'].map(iso_codes)

winners = wcWinnerData[wcWinnerData['Wins'] > 0]

choropleth_fig = px.choropleth(
    winners,
    locations="Code",
    color="Wins",
    hover_name="Team",
    hover_data={
        "Wins": True,
        "Runners-up": True,
        "Total_finals": True,
        "Code": False
    },
    projection="natural earth",
    title="<b>FIFA World Cup Winners (1930-2022)</b>",
    color_continuous_scale=px.colors.sequential.Plasma,
    scope="world",
    height=600
)

choropleth_fig.update_layout(
    margin={"r": 0, "t": 80, "l": 0, "b": 0},
    coloraxis_colorbar=dict(
        title="World Cup Wins",
        thickness=20,
        len=0.75,
        title_font=dict(color='white'),
        tickfont=dict(color='white')
    ),
    geo=dict(
        showframe=False,
        showcoastlines=True,
        landcolor='rgb(40, 40, 40)',
        subunitcolor='rgb(80, 80, 80)',
        bgcolor='rgb(20, 20, 20)'
    ),
    title_font=dict(size=24, color='white'),
    font=dict(family="Arial", size=14, color='white'),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgb(20, 20, 20)'
)

choropleth_fig.update_traces(
    hovertemplate=(
        "<b style='color:white'>%{hovertext}</b><br>"
        "<span style='color:gold'> Wins: %{customdata[0]}</span><br>"
        "<span style='color:silver'> Runners-up: %{customdata[1]}</span><br>"
        "<span style='color:white'>Total Finals: %{customdata[2]}</span>"
    )
)

winning_countries_list = html.Ul([
    html.Li(f"{row['Team']} - {row['Wins']} wins", style={'margin': '10px 0'}) 
    for _, row in winners.sort_values('Wins', ascending=False).iterrows()
], style={'listStyleType': 'none', 'paddingLeft': '0'})

app.layout = html.Div(
    style={'backgroundColor': 'rgb(20, 20, 20)', 'minHeight': '100vh', 'padding': '20px'},
    children=[
        html.H1(
            "FIFA World Cup Visualizations",
            style={
                'textAlign': 'center',
                'color': 'white',
                'marginBottom': '40px',
                'fontFamily': 'Arial'
            }
        ),
        
        # First visualization (choropleth map)
        html.Div(style={'marginBottom': '50px'}, children=[
            html.H2(
                "World Cup Winners Map",
                style={
                    'textAlign': 'center',
                    'color': 'white',
                    'marginBottom': '20px'
                }
            ),
            html.Div(style={'display': 'flex', 'gap': '20px'}, children=[
                html.Div(style={'flex': '2'}, children=[
                    dcc.Graph(
                        figure=choropleth_fig,
                        style={
                            'height': '80vh',
                            'border': '1px solid #444',
                            'borderRadius': '8px'
                        }
                    )
                ]),
                html.Div(style={
                    'flex': '1',
                    'backgroundColor': 'rgb(30, 30, 30)',
                    'padding': '20px',
                    'borderRadius': '8px',
                    'border': '1px solid #444',
                    'color': 'white'
                }, children=[
                    html.H3("Winning Countries", style={'textAlign': 'center', 'marginBottom': '20px'}),
                    winning_countries_list
                ])
            ])
        ]),
        
        # Second visualization (country performance)
        html.Div(style={'marginBottom': '50px'}, children=[
            html.H2(
                "World Cup Performance by Country",
                style={
                    'textAlign': 'center',
                    'color': 'white',
                    'marginBottom': '20px'
                }
            ),
            dcc.Dropdown(
                id='country-dropdown',
                options=[{'label': team, 'value': team} for team in wcWinnerData['Team']],
                value='Brazil',
                style={
                    'width': '50%', 
                    'margin': '0 auto', 
                    'padding': '20px',
                    'color': 'black'
                }
            ),
            dcc.Graph(id='performance-graph')
        ]),
        
        # Third visualization (yearly results)
        html.Div(children=[
            html.H2(
                "World Cup Results by Year",
                style={
                    'textAlign': 'center',
                    'color': 'white',
                    'marginBottom': '20px'
                }
            ),
            dcc.Dropdown(
                id='year-dropdown',
                options=[{'label': str(year), 'value': year} for year in sorted(finals_df['Year'].unique(), reverse=True)],
                value=finals_df['Year'].max(),
                style={'width': '50%', 'margin': '20px auto', 'color': 'black'}
            ),
            html.Div(id='worldcup-result', style={
                'textAlign': 'center',
                'fontSize': '20px',
                'marginTop': '20px',
                'color': 'white'
            })
        ])
    ]
)

@app.callback(
    Output('performance-graph', 'figure'),
    Input('country-dropdown', 'value')
)
def update_graph(selected_country):
    country_data = wcWinnerData[wcWinnerData['Team'] == selected_country]
    
    fig = px.bar(
        country_data,
        x='Team',
        y=['Wins'],
        title=f'{selected_country} World Cup History',
        labels={'value': 'Count', 'variable': 'Result'},
        color_discrete_map={'Wins': 'gold'},
        barmode='group'
    )
    
    fig.update_layout(
        yaxis_title=f"Number of times {selected_country} won the World Cup",
        xaxis_title="",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        title_font_color='white',
        legend_font_color='white',
        xaxis=dict(tickfont=dict(color='white')),
        yaxis=dict(tickfont=dict(color='white'))
    )
    
    return fig

@app.callback(
    Output('worldcup-result', 'children'),
    Input('year-dropdown', 'value')
)
def update_result(selected_year):
    result = finals_df[finals_df['Year'] == selected_year].iloc[0]
    return [
        html.H3(f"{selected_year} World Cup Final"),
        html.P(f"Winner: {result['Winner']}", style={'color': 'gold', 'fontWeight': 'bold'}),
        html.P(f"Runner-up: {result['Runner-up']}", style={'color': 'silver', 'fontWeight': 'bold'})
    ]

if __name__ == '__main__':
    app.run(debug=True)