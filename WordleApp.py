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

### End Panda manipulation ### 

external_stylesheets = [dbc.themes.CYBORG]

app = JupyterDash(__name__, external_stylesheets=external_stylesheets)

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
                    dcc.RadioItems(id='crossfilter-xaxis-column',
                                   options=[{'label': i, 'value': i} for i in player_list],
                                   value='Player1')
                ]),
                html.Div([
                    html.H2(id='total-games-played'),
                    html.H2(id='avg-fails')
                ])
            ],
            style={'width':'49%'}
            ),
            # Right Div
            html.Div([
                html.Div([
                    dcc.Graph(id='bars-fail-total',
                              figure=px.bar(ranking_df,
                                            x="Fails",
                                            y="Name",
                                            color="Name",
                                            text_auto=True)
                             )
                ]),
                html.Div([
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
        text_auto=True
        # barmode="group"
    )
    # now update the figture with a click
    fig.update_layout(transition_duration=250)

    return fig

# update total-games-played
@app.callback(
    Output('total-games-played', 'children'),
    Input('crossfilter-xaxis-column', 'value')
)
def update_total_games(selected_player):
    filtered_value = total_games[ total_games.Name == selected_player ]['PuzzleNum'].values
    return 'Total Games Played: {}'.format(filtered_value[0])

# update avg-fails
@app.callback(
    Output('avg-fails', 'children'),
    Input('crossfilter-xaxis-column', 'value')
)
def update_avg_fails(selected_player):
    filtered_value = avg_fails[ avg_fails.Name == selected_player]['Fails'].values
    return 'Mean Easy Game Fails {:.2f}, Mean Hard Game Fails {:.2f}'.format(filtered_value[0], filtered_value[1])

# update avg-weekly-fails
@app.callback(
    Output('avg-weekly-fails', 'children'), 
    Input('crossfilter-xaxis-column', 'value')
)
def update_avg_weekly_fails(selected_player):
    filtered_value = ranking_df[ ranking_df.Name == selected_player ]['MeanWeeklyFails'].values
    return 'Mean Fails Per Week {:.2f}'.format(filtered_value[0])

if __name__ == '__main__':
    # run better without 'mode="jupyterdash"'
    app.run_server(debug=True, threaded=True)