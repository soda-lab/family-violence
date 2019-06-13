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

month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


events_df = pd.read_csv('events.csv')
events_df['date'] = events_df['date'].astype(str)
events_df.set_index('date', inplace=True)


def get_query(dt):
    year = dt[:4]
    month = dt[4:6]
    day = dt[6:]
    month_label = month_labels[int(month)-1]
    return 'SELECT text, [extended_tweet.full_text] FROM tweets \
        WHERE created_at like "%' + str(year) + '" AND \
        created_at like "%' + month_label + ' ' + day + '%" \
        ORDER BY retweet_count+reply_count DESC LIMIT 5'


conn = sqlite3.connect('dpc.db')


sample_tweets = {}
for date in list(events_df.index):
    paras = []
    query = get_query(date)
    sample_tweets_df = pd.read_sql(query, conn)
    for i, row in sample_tweets_df.iterrows():
        text = str(i + 1) + '. '
        if row['extended_tweet.full_text']:
            text += row['extended_tweet.full_text']
        else:
            text += row['text']
        text = text.replace('amp;', '')
        paras.append(html.P(
            className='card-text',
            children=text
        ))
    sample_tweets[date] = paras


df_count = {}
df_new = {}
count_smoothed = {}
markers = {}

for year in range(2014, 2019):
    query = 'SELECT * FROM count_tweets_daily WHERE date like "%' + str(year) + '%"'

    df = pd.read_sql(query, conn)

    df_count[str(year)] = df.copy()

    if year == 2014:
        count_smoothed[str(year)] = gaussian_filter1d(df['count'], sigma=1)
    else:
        count_smoothed[str(year)] = gaussian_filter1d(df['count'], sigma=3)

    marker = []
    for i, row in df.iterrows():
        if row['date'] in list(events_df.index):
            marker.append(count_smoothed[str(year)][i])
        else:
            marker.append(None)

    markers[str(year)] = marker

    df['date'] = df['date'].map(lambda d: datetime.strptime(d, "%Y%m%d"))
    df_new[str(year)] = df.copy()

conn.close()


color_for_year = {
    '2014': '#800000',
    '2015': '#FF5733',
    '2016': '#008000',
    '2017': '#000080',
    '2018': '#7D3C98'
}


app = dash.Dash(__name__)

app.layout = html.Div(
    className='container-fluid',
    style={'padding-top': '15px', 'margin-top': 'auto'},
    children=[
        html.Div(
            className='row',
            style={'height': '97vh'},
            children=[
                html.Div(
                    className='col-1',
                    style={'margin-top': '9%'},
                    children=[
                        html.Div(
                            className='btn-group-vertical',
                            children=[
                                html.Button(
                                    type='button',
                                    className='btn btn-primary',
                                    id='btn-2014',
                                    n_clicks=0,
                                    children='2014'
                                ),
                                html.Button(
                                    type='button',
                                    className='btn btn-primary',
                                    id='btn-2015',
                                    n_clicks=0,
                                    children='2015'
                                ),
                                html.Button(
                                    type='button',
                                    className='btn btn-primary',
                                    id='btn-2016',
                                    n_clicks=0,
                                    children='2016'
                                ),
                                html.Button(
                                    type='button',
                                    className='btn btn-primary',
                                    id='btn-2017',
                                    n_clicks=0,
                                    children='2017'
                                ),
                                html.Button(
                                    type='button',
                                    className='btn btn-primary',
                                    id='btn-2018',
                                    n_clicks=0,
                                    children='2018'
                                ),
                                html.Button(
                                    type='button',
                                    className='btn btn-info',
                                    id='btn-all',
                                    n_clicks=0,
                                    children='All Years'
                                )
                            ]
                        )
                    ]
                ),
                html.Div(
                    className='col-8',
                    children=[
                        html.Div(
                            className='row',
                            children=[
                                html.Div(
                                    className='btn-group btn-group-toggle',
                                    style={'margin-left': '7.5%'},
                                    children=[
                                        html.Button(
                                            id='btn-line',
                                            n_clicks=0,
                                            className='btn btn-primary active',
                                            children='Line'
                                        ),
                                        html.Button(
                                            id='btn-bar',
                                            n_clicks=0,
                                            className='btn btn-warning',
                                            children='Bar'
                                        )
                                    ]
                                )
                            ]
                        ),
                        html.Div(
                            className='row',
                            children=[
                                dcc.Graph(
                                    id='graph',
                                    config=dict(displayModeBar=False),
                                    style={
                                      'height': '100vh',
                                      'width': '100%'
                                    },
                                    figure={}
                                )
                            ]
                        )
                    ]
                ),
                html.Div(
                    className='col-3',
                    children=[
                        html.Div(
                            className='card text-white bg-primary mb-3',
                            style={'height': '40vh'},
                            children=[
                                html.Div(
                                    className='card-header',
                                    children='Event'
                                ),
                                html.Div(
                                    className='card-body',
                                    style={'overflow-y': 'scroll'},
                                    children=[
                                        html.H4(
                                            id='date',
                                            className='card-title',
                                            children=''
                                        ),
                                        html.Div(
                                            id='event-text',
                                            className='card-text',
                                            children=''
                                        )
                                    ]
                                )
                            ]
                        ),
                        html.Div(
                            className='card text-white bg-primary mb-3',
                            style={'height': '51vh'},
                            children=[
                                html.Div(
                                    className='card-header',
                                    children='Sample Tweets'
                                ),
                                html.Div(
                                    id='tweets-div',
                                    style={'overflow-y': 'scroll'},
                                    className='card-body',
                                    children=[]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)


def transform_date(d):
    return month_labels[int(d[4:6])-1] + ' ' + d[6:]


comparison_data = []
for year in range(2014, 2019):
    df = df_count[str(year)].copy()
    if year == 2016:
        df.drop(df[df['date'] == '20160229'].index, inplace=True)
    df['date'] = df['date'].map(lambda d: transform_date(d))
    comparison_data.append(go.Scatter(
        x=df['date'],
        y=count_smoothed[str(year)],
        mode='lines',
        stackgroup=str(year),
        name=str(year)
    ))
comparison_graph = {
    'data': comparison_data,
    'layout': dict(
        title='2014-2018 Comparison',
        # height='100%',
        xaxis=dict(
            rangeslider=dict(
                visible=True
            )
        ),
        font=dict(family='Montserrat')
    )
}


def get_layout(year):
    return {
        'title': year,
        # 'height': '100%',
        'font': dict(family='Montserrat'),
        'xaxis': dict(
            rangeselector=dict(
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


def get_yearly_graph(year):
    if year != 0:
        year = str(year)
        return {
            'data': [
                go.Scatter(
                    x=df_new[year]['date'],
                    y=count_smoothed[year],
                    line=dict(
                        width=3,
                        color=color_for_year[str(year)]
                    ),
                    fill='tozeroy',
                    opacity=0.8,
                    hoverinfo='x+y',
                    showlegend=False
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
            'layout': get_layout(year)
        }
    else:
        return comparison_graph


def get_yearly_bar(year):
    if year != 0:
        year = str(year)
        return {
            'data': [
                go.Bar(
                    x=df_new[year]['date'],
                    y=df_new[year]['count'],
                    marker=dict(
                        color=color_for_year[str(year)]
                    ),
                    showlegend=False
                )
            ],
            'layout': get_layout(year)
        }
    else:
        return comparison_graph


previous_n_clicks_2014 = 0
previous_n_clicks_2015 = 0
previous_n_clicks_2016 = 0
previous_n_clicks_2017 = 0
previous_n_clicks_2018 = 0
previous_n_clicks_all = 0
previous_n_clicks_line = 0
previous_n_clicks_bar = 0
previous_n_clicks_line_for_update_line = 0
previous_n_clicks_bar_for_update_line = 0
previous_n_clicks_line_for_update_bar = 0
previous_n_clicks_bar_for_update_bar = 0
current_mode = 'line'
current_year = 2014


@app.callback(
    dash.dependencies.Output('graph', 'figure'),
    [dash.dependencies.Input('btn-2014', 'n_clicks'),
     dash.dependencies.Input('btn-2015', 'n_clicks'),
     dash.dependencies.Input('btn-2016', 'n_clicks'),
     dash.dependencies.Input('btn-2017', 'n_clicks'),
     dash.dependencies.Input('btn-2018', 'n_clicks'),
     dash.dependencies.Input('btn-all', 'n_clicks'),
     dash.dependencies.Input('btn-line', 'n_clicks'),
     dash.dependencies.Input('btn-bar', 'n_clicks')]
)
def update_graph(
        n_clicks_2014,
        n_clicks_2015,
        n_clicks_2016,
        n_clicks_2017,
        n_clicks_2018,
        n_clicks_all,
        n_clicks_line,
        n_clicks_bar
):

    def is_initial():
        if (
            n_clicks_2014 == 0
            and n_clicks_2015 == 0
            and n_clicks_2016 == 0
            and n_clicks_2017 == 0
            and n_clicks_2018 == 0
            and n_clicks_all == 0
            and n_clicks_line == 0
            and n_clicks_bar == 0
        ):
            return True
        else:
            return False

    global previous_n_clicks_2014
    global previous_n_clicks_2015
    global previous_n_clicks_2016
    global previous_n_clicks_2017
    global previous_n_clicks_2018
    global previous_n_clicks_all
    global previous_n_clicks_line
    global previous_n_clicks_bar
    global current_year
    global current_mode

    if is_initial():
        return get_yearly_graph(2014)
    else:
        if n_clicks_2014 > previous_n_clicks_2014:
            previous_n_clicks_2014 = n_clicks_2014
            current_year = 2014
            if current_mode == 'line':
                return get_yearly_graph(2014)
            else:
                return get_yearly_bar(2014)
        elif n_clicks_2015 > previous_n_clicks_2015:
            previous_n_clicks_2015 = n_clicks_2015
            current_year = 2015
            if current_mode == 'line':
                return get_yearly_graph(2015)
            else:
                return get_yearly_bar(2015)
        elif n_clicks_2016 > previous_n_clicks_2016:
            previous_n_clicks_2016 = n_clicks_2016
            current_year = 2016
            if current_mode == 'line':
                return get_yearly_graph(2016)
            else:
                return get_yearly_bar(2016)
        elif n_clicks_2017 > previous_n_clicks_2017:
            previous_n_clicks_2017 = n_clicks_2017
            current_year = 2017
            if current_mode == 'line':
                return get_yearly_graph(2017)
            else:
                return get_yearly_bar(2017)
        elif n_clicks_2018 > previous_n_clicks_2018:
            previous_n_clicks_2018 = n_clicks_2018
            current_year = 2018
            if current_mode == 'line':
                return get_yearly_graph(2018)
            else:
                return get_yearly_bar(2018)
        elif n_clicks_all > previous_n_clicks_all:
            previous_n_clicks_all = n_clicks_all
            current_year = 0
            return get_yearly_graph(0)
        elif n_clicks_line > previous_n_clicks_line:
            previous_n_clicks_line = n_clicks_line
            current_mode = 'line'
            return get_yearly_graph(current_year)
        elif n_clicks_bar > previous_n_clicks_bar:
            previous_n_clicks_bar = n_clicks_bar
            current_mode = 'bar'
            return get_yearly_bar(current_year)


@app.callback(
    dash.dependencies.Output('btn-line', 'className'),
    [dash.dependencies.Input('btn-line', 'n_clicks'),
     dash.dependencies.Input('btn-bar', 'n_clicks')]
)
def update_line_btn(n_clicks_line, n_clicks_bar):
    global previous_n_clicks_line_for_update_line
    global previous_n_clicks_bar_for_update_line
    if n_clicks_line == 0 and n_clicks_bar == 0:
        return 'btn btn-primary active'
    else:
        if n_clicks_line > previous_n_clicks_line_for_update_line:
            previous_n_clicks_line_for_update_line = n_clicks_line
            return 'btn btn-primary active'
        else:
            previous_n_clicks_bar_for_update_line = n_clicks_bar
            return 'btn btn-primary'


@app.callback(
    dash.dependencies.Output('btn-bar', 'className'),
    [dash.dependencies.Input('btn-line', 'n_clicks'),
     dash.dependencies.Input('btn-bar', 'n_clicks')]
)
def update_line_btn(n_clicks_line, n_clicks_bar):
    global previous_n_clicks_line_for_update_bar
    global previous_n_clicks_bar_for_update_bar
    if n_clicks_line == 0 and n_clicks_bar == 0:
        return 'btn btn-primary'
    else:
        if n_clicks_line > previous_n_clicks_line_for_update_bar:
            previous_n_clicks_line_for_update_bar = n_clicks_line
            return 'btn btn-primary'
        else:
            previous_n_clicks_bar_for_update_bar = n_clicks_bar
            return 'btn btn-primary active'


@app.callback(
    dash.dependencies.Output('date', 'children'),
    [dash.dependencies.Input('graph', 'clickData')])
def display_click_data(click_data):
    if not click_data:
        return ''
    dt = click_data['points'][0]['x']
    return dt


@app.callback(
    dash.dependencies.Output('event-text', 'children'),
    [dash.dependencies.Input('graph', 'clickData')])
def display_click_data(click_data):
    if not click_data:
        return ''
    dt = click_data['points'][0]['x'].replace('-', '')
    if dt in list(events_df.index):
        return events_df.loc[dt]['event']
    else:
        return ''


@app.callback(
    dash.dependencies.Output('tweets-div', 'children'),
    [dash.dependencies.Input('graph', 'clickData')])
def display_click_data(click_data):
    if not click_data:
        return ''
    dt = click_data['points'][0]['x'].replace('-', '')
    if dt in list(events_df.index):
        return sample_tweets[dt]
    else:
        return ''


if __name__ == '__main__':
    app.run_server(debug=True)
