import pandas as pd
import sqlite3
import plotly.graph_objs as go
from datetime import datetime
import warnings
import dash
import dash_core_components as dcc
import dash_html_components as html
from scipy.ndimage.filters import gaussian_filter1d

warnings.filterwarnings("ignore", category=UserWarning)


conn = sqlite3.connect('dpc.db')

df_count = {}
df_new = {}
count_smoothed = {}
markers = {}

for year in range(2014, 2019):
    query = 'SELECT * FROM count_tweets_daily WHERE date like "%' + str(year) + '%"'

    df = pd.read_sql(query, conn)

    df_count[str(year)] = df.copy()

    count_smoothed[str(year)] = gaussian_filter1d(df['count'], sigma=3)

    marker = []
    for _, row in df.iterrows():
        if row['date'] == '20181112':
            marker.append(249)
        elif row['date'] == '20181123':
            marker.append(260)
        else:
            marker.append(None)

    markers[str(year)] = marker

    df['date'] = df['date'].map(lambda d: datetime.strptime(d, "%Y%m%d"))
    df_new[str(year)] = df.copy()

conn.close()


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div(children=[
    html.H1(
        children='Twitter Timeline',
        style={
            'textAlign': 'center'
        }
    ),

    html.Div(
        style={'margin': '20px'},
        children=[
            html.Div(
                style={
                    'width': '7%',
                    'float': 'left',
                    'margin-top': '60px'
                },
                children=[
                    html.Button(children='2014', style={
                        'width': '90px'
                    }),
                    html.Button(children='2015', style={
                        'margin-top': '20px',
                        'width': '90px'
                    }),
                    html.Button(children='2016', style={
                        'margin-top': '20px',
                        'width': '90px'
                    }),
                    html.Button(children='2017', style={
                        'margin-top': '20px',
                        'width': '90px'
                    }),
                    html.Button(children='2018', style={
                        'margin-top': '20px',
                        'width': '90px'
                    }),
                    html.Button(
                        id='button-all',
                        n_clicks=0,
                        children='All',
                        style={
                            'margin-top': '20px',
                            'width': '90px'
                    })
                ]
            ),

            html.Div(
                style={
                    'float': 'left',
                    'margin-left': '8px',
                    'width': '75%'
                },
                children=[
                    dcc.Graph(
                        id='graph',
                        figure={}
                    )
                ]
            ),

            html.Div(
                style={
                    'float': 'right',
                    'width': '16%',
                    'height': '500px',
                    'border': '1px solid #A6ACAF',
                    'border-radius': 10
                },
                children=[
                    html.Div(
                        style={
                            'margin': '2%',
                            'height': '40%',
                            'border-bottom': '1px solid #A6ACAF'
                        },
                        children=[
                            html.Span(
                                children=[
                                    html.Label(
                                        style={'float': 'left', 'font-weight': 'bold'},
                                        children='Date:'
                                    ),
                                    html.Label(
                                        style={
                                            'position': 'relative',
                                            'left': '10px',
                                            'font-weight': 'bold'
                                        },
                                        children='1 Jan 2018'
                                    )
                                ]
                            ),
                            html.P(
                                style={
                                    'overflow-y': 'scroll',
                                    'margin-top': '10px'
                                },
                                children='Morrison was elected prime minister again...'
                            )
                        ]
                    ),

                    html.Div(
                        style={
                            'margin': '2%',
                            'height': '60%',
                        },
                        children=[
                            html.Label(
                                style={'font-weight': 'bold'},
                                children='Sample Tweets:'
                            ),

                            html.P(
                                style={
                                    'overflowY': 'scroll',
                                    'margin-top': '10px'
                                },
                                children='@abc @eft This is a great day la lol asd ???? asdasffdfsfsd'
                            )
                        ]
                    )
                ]
            )
        ]
    )
])


def get_yearly_graph(year):
    year = str(year)
    return {
        'data': [
            go.Scatter(
                x=df_new[year]['date'],
                y=count_smoothed[year],
                line=dict(
                    width=3,
                    color='#FF5733'
                ),
                opacity=0.8,
                showlegend=False,
                hoverinfo='x+y'
            ),
            go.Scatter(
                x=df_new[year]['date'],
                y=markers[year],
                mode='markers',
                marker=dict(
                    symbol='square',
                    size=9,
                    color='rgba(152, 0, 0, .8)'
                ),
                showlegend=False,
                hoverinfo='none'
            )
        ],
        'layout': {
            'title': year,
            'height': 500,
            'xaxis': dict(
                rangeselector=dict(

                    # Adjust date range - 7 days, 14 days, all days
                    buttons=list([
                        dict(count=1,
                             label='1m',
                             step='month',
                             stepmode='backward'),
                        dict(count=3,
                             label='3m',
                             step='month',
                             stepmode='backward'),
                        dict(step='all')
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type='date'
            )
        }
    }


month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def transform_date(d):
    return month_labels[int(d[4:6])-1] + ' ' + d[6:]


@app.callback(
    dash.dependencies.Output('graph', 'figure'),
    [dash.dependencies.Input('button-all', 'n_clicks')]
)
def update_graph(n_clicks):
    if n_clicks == 0:
        return get_yearly_graph(2018)
    else:
        data = []
        for year in range(2014, 2019):
            df = df_count[str(year)].copy()
            if year == 2016:
                df.drop(df[df['date'] == '20160229'].index, inplace=True)
            df['date'] = df['date'].map(lambda d: transform_date(d))
            data.append(go.Scatter(
                x=df['date'],
                y=count_smoothed[str(year)],
                line=dict(width=3),
                name=str(year)
            ))
        return {
            'data': data,
            'layout': dict(
                title='2014-2018 Comparison',
                height=500
            )
        }


if __name__ == '__main__':
    app.run_server(debug=True)
