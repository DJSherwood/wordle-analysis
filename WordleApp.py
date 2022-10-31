# import libraries
import pandas as pd
from jupyter_dash import JupyterDash
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import censoring

# configure for JupyterDash
JupyterDash.infer_jupyter_proxy_config()

### Perform panda manipulation here ###

df = pd.read_csv(censoring.wordle_output)

# limit to the puzzle in which we last have words (396)
df = df[ (df['PuzzleNum'] < 467) & 
         (df['PuzzleNum'] != 421) & 
         (df['Difficulty'] != 'Undefined')].copy()

# make player list
player_list = ['Player1','Player2','Player3','Player4','Player5','Player6']

# focus on puzzles which have all 6 players
df = df[ df['Name'].isin(player_list) ].copy()
B = df.groupby(['PuzzleNum']).agg({'Name':'count'}).reset_index()
C = B[ B['Name'] == 6 ].copy()
df2 = df[ df['PuzzleNum'].isin(C['PuzzleNum'].to_list())]

# make sure date time is correct type
#df2['Date_Time']= pd.to_datetime(df2['Date_Time'])

# static ranking data frame
ranking_df = df2.groupby(['Name']).agg({'Fails':'sum'}).reset_index()
ranking_df = ranking_df.sort_values(by=['Fails'], ascending=True)

# static total games data frame
total_games = df2.groupby(['Name','PuzzleNum']).size().reset_index().groupby('Name').count().reset_index()

# static fails by difficulty data frame
avg_fails = df2.groupby(['Name','Difficulty']).agg({'Fails': 'mean'}).reset_index().sort_values(['Name'])

# load predictions
preds = pd.read_csv(censoring.predictions)

# load model output
model_output = pd.read_csv(censoring.model_output)

### End Panda manipulation ### 
app = JupyterDash(__name__, external_stylesheets= [dbc.themes.CYBORG])

# Create server variable with Flask server object for use with gunicorn
server = app.server

# Master Div
app.layout = html.Div(
    children=[
        html.H1(children='Wordle Ranking & Performance'),
        html.Div([ 
            # Left Div
            html.Div([
                html.Div([
                    html.H4("Choose Player"),
                    dcc.Dropdown(id='crossfilter-xaxis-column',
                                   options=[{'label': i, 'value': i} for i in player_list],
                                   value='Player1')
                ]),
                html.Div([
                    html.H4('Total Games Played'),
                    html.H2(id='total-games-played')
                ],
                    style={'display':'flex'}
                ),
                # create div for averages
                html.Div([
                    # now create div for easy
                    html.Div([
                        html.H4("Avg. 'Easy' Fails"),
                        html.H2(id='avg-fails-easy')
                    ]),
                    # now create div for hard
                    html.Div([
                        html.H4("Avg. 'Hard' Fails"),
                        html.H2(id='avg-fails-hard')
                    ])
                ],
                    style={'display':'flex'}
                ),
                # create div for predictions
                html.Div([
                    # now create div for easy
                    html.Div([
                        html.H4("Pred. 'Easy' Fails"),
                        html.H2(id='model-preds-easy')
                    ]),
                    # now create div for hard
                    html.Div([
                        html.H4("Pred. 'Hard' Fails"),
                        html.H2(id='model-preds-hard')
                    ])
                ],
                    style={'display':'flex'}
                ),
                # graph of BetaBinomial using found parameters
                html.Div([
                    html.H4("Predicted Failure Density"),
                    dcc.Graph(id='model-output')
                ])
            ],
            style={'width':'49%'}
            ),
            # Right Div
            html.Div([
                html.Div([
                    html.H4("Ranking"),
                    dcc.Graph(id='bars-fail-total',
                              figure=px.bar(ranking_df,
                                            x="Fails",
                                            y="Name",
                                            color="Name",
                                            text_auto=True).update_layout({
                                  'plot_bgcolor': 'rgba(0, 0, 0, 0)',
                                  'paper_bgcolor': 'rgba(0, 0, 0, 0)',
                                  'font': { 'color': '#FFFFFF', 'size':12},
                                  'showlegend': False,
                                  })
                             )
                ]),
                html.Div([
                    html.H4("Guess Distribution"),
                    dcc.Graph(id='bars-fail-distribution')
                ])
            ],
                style={'width':'49%'}
            )
        ],
            style={'display': 'flex'}
        )
    ]
)


# update bars-fail-distribution
@app.callback(
    Output('bars-fail-distribution', 'figure'),
    Input('crossfilter-xaxis-column', 'value')
)
def update_distplot(selected_player):
    # input filters df onto a single name
    filtered_df = df2[ df2.Name == selected_player ]
    fig = px.histogram(
        filtered_df, 
        x="Fails", 
        # y="Counts", 
        color="Difficulty", 
        facet_col="Difficulty",
        text_auto=True
        # barmode="group"
    )
    # now update the figture with a click
    fig.update_layout(
        {'plot_bgcolor': 'rgba(0, 0, 0, 0)',
         'paper_bgcolor': 'rgba(0, 0, 0, 0)',
         'font': { 'color': '#FFFFFF', 'size':12}
        },
        transition_duration=250
    )
    
    fig.update_yaxes(range=[0.0, 40.0], showgrid=False)
    fig.update_xaxes(showgrid=False)

    return fig
            
            
@app.callback(
    Output('model-output', 'figure'),
    Input('crossfilter-xaxis-column', 'value')
)
def update_density(selected_player):
    filtered_df = model_output[ model_output.Name == selected_player ]
    fig = px.area(
        filtered_df, 
        x="Fails", 
        y="Density",
        color="Difficulty",
        # line_group="Difficulty",
        facet_col="Difficulty"
    )
    # now update the figure with a click
    fig.update_layout(
        {'plot_bgcolor': 'rgba(0, 0, 0, 0)',
         'paper_bgcolor': 'rgba(0, 0, 0, 0)',
         'font': { 'color': '#FFFFFF', 'size':12}
        },
        transition_duration=250
    )
    fig.update_yaxes(range=[0.0, 0.5],showgrid=False)
    fig.update_xaxes(showgrid=False)
    
    return fig

# update total-games-played
@app.callback(
    Output('total-games-played', 'children'),
    Input('crossfilter-xaxis-column', 'value')
)
def update_total_games(selected_player):
    filtered_value = total_games[ total_games.Name == selected_player ]['PuzzleNum'].values
    return '{}'.format(filtered_value[0])

# update avg-fails
@app.callback(
    Output('avg-fails-easy', 'children'),
    Input('crossfilter-xaxis-column', 'value')
)
def update_avg_fails(selected_player):
    filtered_value = avg_fails[ avg_fails.Name == selected_player]['Fails'].values
    return '{:.2f}'.format(filtered_value[0])

# update avg-fails
@app.callback(
    Output('avg-fails-hard', 'children'),
    Input('crossfilter-xaxis-column', 'value')
)
def update_avg_fails(selected_player):
    filtered_value = avg_fails[ avg_fails.Name == selected_player]['Fails'].values
    return '{:.2f}'.format(filtered_value[1])

# update model predictions
@app.callback(
    Output('model-preds-easy','children'),
    Input('crossfilter-xaxis-column', 'value')
)
def update_model_preds(selected_player):
    filtered_value = preds[ preds.Players == selected_player]['prediction'].values
    return '{:.2f}'.format(filtered_value[0])

@app.callback(
    Output('model-preds-hard','children'),
    Input('crossfilter-xaxis-column', 'value')
)
def update_model_preds(selected_player):
    filtered_value = preds[ preds.Players == selected_player]['prediction'].values
    return '{:.2f}'.format(filtered_value[1])


if __name__ == '__main__':
    # run better without 'mode="jupyterdash"'
    app.run_server(debug=True, threaded=True)