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

    if year == 2014:
        count_smoothed[str(year)] = gaussian_filter1d(df['count'], sigma=1)
    else:
        count_smoothed[str(year)] = gaussian_filter1d(df['count'], sigma=3)

    marker = []
    for _, row in df.iterrows():
        if row['date'] == '20140928':
            marker.append(36)
        elif row['date'] == '20141125':
            marker.append(84)
        elif row['date'] == '20181112':
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

color_for_year = {
    '2014': '#800000',
    '2015': '#FF5733',
    '2016': '#008000',
    '2017': '#000080',
    '2018': '#7D3C98'
}

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.Span(
        children=[
            html.Button(
                id='btn-line',
                n_clicks=0,
                style={},
                children='Line'
            ),
            html.Button(
                id='btn-bar',
                n_clicks=0,
                style={},
                children='Bar'
            )
        ]
    ),
    html.Div(
        children=[
            html.Div(
                style={
                    'width': '7%',
                    'float': 'left',
                    'margin-top': "7%"
                },
                children=[
                    html.Button(id='btn-2014', n_clicks=0, children='2014', style={
                        'width': '90px'
                    }),
                    html.Button(id='btn-2015', n_clicks=0,  children='2015', style={
                        'margin-top': '20px',
                        'width': '90px'
                    }),
                    html.Button(id='btn-2016', n_clicks=0,  children='2016', style={
                        'margin-top': '20px',
                        'width': '90px'
                    }),
                    html.Button(id='btn-2017', n_clicks=0,children='2017', style={
                        'margin-top': '20px',
                        'width': '90px'
                    }),
                    html.Button(id='btn-2018', n_clicks=0,children='2018', style={
                        'margin-top': '20px',
                        'width': '90px'
                    }),
                    html.Button(
                        id='btn-all',
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
                        config=dict(displayModeBar=False),
                        figure={}
                    )
                ]
            ),

            html.Div(
                style={
                    'float': 'right',
                    'width': '17%',
                    'height': '500px',
                    'border': '1px solid #A6ACAF',
                    'border-radius': 10
                },
                children=[
                    html.Div(
                        style={
                            'margin': '2%',
                            'height': '40%',
                            'border-bottom': '1px solid #A6ACAF',
                            'overflow-x': 'hidden',
                            'overflow-y': 'scroll'
                        },
                        children=[
                            html.Span(
                                children=[
                                    html.Label(
                                        style={'float': 'left', 'font-weight': 'bold'},
                                        children='Date:'
                                    ),
                                    html.Label(
                                        id='date-label',
                                        style={
                                            'position': 'relative',
                                            'left': '10px',
                                            'font-weight': 'bold'
                                        },
                                        children=''
                                    )
                                ]
                            ),
                            html.P(
                                id='event-text',
                                style={
                                    'margin-top': '10px'
                                },
                                children='Morrison was elected prime minister again...'
                            )
                        ]
                    ),

                    html.Div(
                        style={
                            'margin': '2%',
                            'height': '55%',
                            'overflow-y': 'scroll'
                        },
                        children=[
                            html.Label(
                                style={'font-weight': 'bold'},
                                children='Sample Tweets:'
                            ),

                            html.P(
                                id='sample-text',
                                style={
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

month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


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
        fill='tozeroy',
        name=str(year)
    ))
comparison_graph = {
    'data': comparison_data,
    'layout': dict(
        title='2014-2018 Comparison',
        height=550,
        xaxis=dict(
            rangeslider=dict(
                visible=True
            )
        )
    )
}


def get_layout(year):
    return {
        'title': year,
        'height': 550,
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
    dash.dependencies.Output('btn-line', 'style'),
    [dash.dependencies.Input('btn-line', 'n_clicks'),
     dash.dependencies.Input('btn-bar', 'n_clicks')]
)
def update_line_btn(n_clicks_line, n_clicks_bar):
    global previous_n_clicks_line_for_update_line
    global previous_n_clicks_bar_for_update_line
    if n_clicks_line == 0 and n_clicks_bar == 0:
        return {
            'margin-left': '13%',
            'width': '90px',
            'background-color': '#5DADE2'
        }
    else:
        if n_clicks_line > previous_n_clicks_line_for_update_line:
            previous_n_clicks_line_for_update_line = n_clicks_line
            return {
                'margin-left': '13%',
                'width': '90px',
                'background-color': '#5DADE2'
            }
        else:
            previous_n_clicks_bar_for_update_line = n_clicks_bar
            return {
                'margin-left': '13%',
                'width': '90px',
                'background-color': 'white'
            }


@app.callback(
    dash.dependencies.Output('btn-bar', 'style'),
    [dash.dependencies.Input('btn-line', 'n_clicks'),
     dash.dependencies.Input('btn-bar', 'n_clicks')]
)
def update_line_btn(n_clicks_line, n_clicks_bar):
    global previous_n_clicks_line_for_update_bar
    global previous_n_clicks_bar_for_update_bar
    if n_clicks_line == 0 and n_clicks_bar == 0:
        return {
            'margin-left': 0,
            'width': '90px',
            'background-color': 'white'
        }
    else:
        if n_clicks_line > previous_n_clicks_line_for_update_bar:
            previous_n_clicks_line_for_update_bar = n_clicks_line
            return {
                'margin-left': 0,
                'width': '90px',
                'background-color': 'white'
            }
        else:
            previous_n_clicks_bar_for_update_bar = n_clicks_bar
            return {
                'margin-left': 0,
                'width': '90px',
                'background-color': '#5DADE2'
            }


@app.callback(
    dash.dependencies.Output('date-label', 'children'),
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
    dt = click_data['points'][0]['x']
    if dt == '2014-09-28':
        return 'There was news about the Royal Women’s setting up a program, a taskforce in \
        Queensland, and an NFL commissioner talking about a hotline.'
    elif dt == '2014-11-25':
        return [
            html.P('1. National walk against family violence event.'),
            html.P('2. Tony Abbott news about how he hit the wall beside a woman to intimidate her.')
        ]
    elif dt == '2018-11-12':
        return 'Something happened today'
    elif dt == '2018-11-23':
        return 'Some other things happened today'
    else:
        return ''


@app.callback(
    dash.dependencies.Output('sample-text', 'children'),
    [dash.dependencies.Input('graph', 'clickData')])
def display_click_data(click_data):
    if not click_data:
        return ''
    dt = click_data['points'][0]['x']
    if dt == '2014-09-28':
        return [
            html.P("1. Don't get distracted worrying bout Muslims who are JUST PEOPLE worry that 1 woman a week is \
            killed thru domestic violence every week in Oz."),
            html.P("2. \"Don't be a bystander & take any opportunity to (ask) 'Are you OK?'\" urges Quentin Bryce \
            on #domesticviolence: http://t.co/GSTCN7CXsp"),
            html.P("3. Royal Women's Hospital service offering legal advice to #domestic #violence victims could expand\
             http://t.co/PhXULdYZlH #NoToVAW"),
            html.P("4. Great article highlighting our work w/ @thewomens supporting women experiencing domestic viole\
            nce & training staff http://t.co/1Jbhm7tgTY"),
            html.P("5. Queensland taskforce 'gravely worried' about domestic violence severity http://t.co/AeObieIbQN")
        ]
    elif dt == '2014-11-25':
        return [
            html.P("1. One woman a week dies from domestic violence in Australia. Appalling. #theprojecttv"),
            html.P("2. Infographic: domestic violence in Aust. #WhiteRibbonDay https://t.co/ggDxi4Mm0G http://t.co/i2Z\
            slGVqBO"),
            html.P("3. Men: it's #WhiteRibbonDay - have you taken the oath against domestic violence yet? http://t.co/\
            SJbVP4FmsF http://t.co/3FCsqgjRcn"),
            html.P("4. On #WhiteRibbonDay, we look at the invaluable work of @AssistASista in helping domestic violenc\
            e survivors rebuild their lives #theprojecttv"),
            html.P("5. It's #WhiteRibbonDay & we're proud to recognise @RosieBatty1 & her inspirational campai\
            gn against domestic violence. http://t.co/VCOQDr2SyV")
        ]
    elif dt == '2018-11-12':
        return 'Something sample tweets'
    elif dt == '2018-11-23':
        return 'Some other tweets'
    else:
        return ''


if __name__ == '__main__':
    app.run_server(debug=True)
