import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash
import scipy.integrate as integrate
import math
import numpy as np
import os
import datetime
import json
import requests

# today's date
today = str(datetime.date.today())

# making directories


def make_directory(name):
    parent_dir = "./data"
    path = os.path.join(parent_dir, name)
    try:
        os.mkdir(path)
    except OSError as error:
        print(error)


make_directory(today + '-data')
make_directory('outputs')
make_directory('outputs/'+today+'output')

request_headers = {
    'Host': 'www.nseindia.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}
nse_url = 'https://www.nseindia.com/'


def fetch_data(scrip):
    try:
        perf = {}

        with open('./data/' + today + '-data/fno_data_' + scrip + '.json') as g:
            perf = json.load(g)

        return perf
    except:
        fno_data_url = 'https://www.nseindia.com/api/quote-derivative?symbol=' + \
            requests.utils.quote(scrip)
        resp = requests.get(url=nse_url, headers=request_headers)
        if resp.ok:
            req_cookies = dict(
                nsit=resp.cookies['nsit'], nseappid=resp.cookies['nseappid'], ak_bmsc=resp.cookies['ak_bmsc'])
            response = requests.get(
                url=fno_data_url, headers=request_headers, cookies=req_cookies).json()
            with open('./data/' + today + '-data/fno_data_' + scrip + '.json', 'w') as f:
                json.dump(response, f)

        with open('./data/' + today + '-data/fno_data_' + scrip + '.json') as g:
            perf = json.load(g)

        return perf


def expiry(scrip):
    perf = fetch_data(scrip)

    # listing all expiry dates
    dates = list(dict.fromkeys(perf['expiryDates']))

    # ther are three differnt expiry options contract
    return dates[0]


def labels(scrip):
    perf = fetch_data(scrip)
    exp = expiry(scrip)

    labels = []

    # listing strikes price in sorted order
    for i in perf['stocks']:
        if i['metadata']['expiryDate'] == exp:
            labels.append(i['metadata']['strikePrice'])

    labels = list(dict.fromkeys(labels))
    labels.sort()

    return labels


def data_count(scrip, type, value):
    oi = []
    perf = fetch_data(scrip)
    label = labels(scrip)
    exp = expiry(scrip)

    for i in label:
        temp = len(oi)
        for j in perf['stocks']:
            if j['metadata']['expiryDate'] == exp and j['metadata']['optionType'] == type:
                if str(j['metadata']['strikePrice']) == str(i):
                    if value != 'lastPrice':
                        oi.append(j['marketDeptOrderBook']
                                  ['tradeInfo'][value])
                    else:
                        oi.append(j['metadata'][value])

        if temp == len(oi):
            oi.append(0)

    return oi


def probability(scrip):
    nearest = []
    perf = fetch_data(scrip)
    underlyingValue = perf['underlyingValue']
    strikePrices = perf['strikePrices']
    strikePrices = list(dict.fromkeys(strikePrices))

    label = labels(scrip)
    exp = expiry(scrip)

    l = 0
    for i in strikePrices:
        nearest.append(i - underlyingValue)

    for i in nearest:
        if i < 0:
            nearest[l] = nearest[l] * -1
            l = l + 1

    value = strikePrices[nearest.index(min(nearest))]

    for j in perf['stocks']:
        if j['metadata']['expiryDate'] == exp and j['metadata']['strikePrice'] == value:
            if j['metadata']['optionType'] == 'Call':
                iv_call = j['marketDeptOrderBook']['otherInfo']['impliedVolatility']
            if j['metadata']['optionType'] == 'Put':
                iv_put = j['marketDeptOrderBook']['otherInfo']['impliedVolatility']

    prob = []
    daysexpiry = (datetime.datetime.strptime(exp, '%d-%b-%Y') -
                  datetime.datetime.strptime(today, '%Y-%m-%d')).days

    for i in label:
        # STRIKE<VALUE WIN PROB => NORMSDIST(LN(STRIKEPRICE/VALUE)/CALLIV*SQRT(DAYSTOEXPIRATION/365))
        # normsdist = (1/2pi)^2 * e^(-(z^2)/2)
        if i < value and i > 0:
            try:
                normsdist = math.log(i/underlyingValue) / \
                    ((iv_call/100)*math.sqrt(daysexpiry/365))
                result = integrate.quad(lambda q: (
                    (1/math.sqrt(2 * math.pi))*((math.e)**(q**2/-2.0))), -np.inf, normsdist)
                prob.append(100 - result[0]*100)
            except:
                prob.append(0)
        elif i > value and i > 0:
            try:
                normsdist = math.log(i/underlyingValue) / \
                    ((iv_put/100)*math.sqrt(daysexpiry/365))
                result = integrate.quad(lambda q: (
                    (1/math.sqrt(2 * math.pi))*((math.e)**(q**2/-2.0))), -np.inf, normsdist)
                prob.append(result[0]*100)
            except:
                prob.append(0)
        else:
            prob.append(0)

    return prob


def pcr(scrip):
    j = 0
    ratio = []
    call = data_count(scrip, 'Call', 'openInterest')
    put = data_count(scrip, 'Put', 'openInterest')
    label = labels(scrip)

    for i in label:
        if call[j] == 0:
            ratio.append(1)
        else:
            if put[j]/call[j] > 10:
                ratio.append(-1)
            else:
                ratio.append(put[j]/call[j])
        j = j + 1

    return ratio


def maxpain(scrip):

    call = data_count(scrip, 'Call', 'openInterest')
    put = data_count(scrip, 'Put', 'openInterest')
    label = labels(scrip)

    for i in labels:
        max_l = 0

        for k in range(0, labels.index(i) + 1):
            max_l = max_l + (i - labels[k])*call[k]

        for k in range(labels.index(i), len(labels)):
            max_l = max_l + (labels[k] - i)*put[k]

        maxpain.append(max_l)

    minpos = maxpain.index(min(maxpain))


app = dash.Dash('Optionchain', external_stylesheets=[
                'https://codepen.io/chriddyp/pen/bWLwgP.css'])


# bringing data in memory
with open('fno.json') as g:
  fno_scrips = json.load(g)


app.layout = html.Div([
    dcc.Dropdown(
        id='scrip',
        options=fno_scrips,
        value=''
    ),

    dcc.Tabs([
        dcc.Tab(label='Call & Put', children=[
            dcc.Graph(id='callput')
        ]),
        dcc.Tab(label='PCR', children=[
            dcc.Graph(id="pcr")
        ]),
        dcc.Tab(label='Change', children=[
            dcc.Graph(id="change")
        ]),
        dcc.Tab(label='LTP', children=[
            dcc.Graph(id="ltp")
        ]),
        dcc.Tab(label='Probability', children=[
            dcc.Graph(id="probab")
        ]),
    ])
], style={'width': '500'})


@ app.callback(Output('callput', 'figure'), [Input('scrip', 'value')])
def update_graph(selected_dropdown_value):
    return {
        'data': [{
            'x': labels(selected_dropdown_value),
            'y': data_count(selected_dropdown_value, 'Call', 'openInterest'),
            'type': 'bar', 'name': 'call'
        },
            {
            'x': labels(selected_dropdown_value),
            'y': data_count(selected_dropdown_value, 'Put', 'openInterest'),
            'type': 'bar', 'name': 'put'
        }
        ],
        'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}
    }


@ app.callback(Output('pcr', 'figure'), [Input('scrip', 'value')])
def update_graph(selected_dropdown_value):
    return {
        'data': [{
            'x': labels(selected_dropdown_value),
            'y': pcr(selected_dropdown_value),
            'type': 'scatter', 'name': 'pcr'
        }],
        'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}
    }


@ app.callback(Output('change', 'figure'), [Input('scrip', 'value')])
def update_graph(selected_dropdown_value):
    return {
        'data': [{
            'x': labels(selected_dropdown_value),
            'y': data_count(selected_dropdown_value, 'Call', 'changeinOpenInterest'),
            'type': 'bar', 'name': 'call-changeinOpenInterest'
        },
            {
            'x': labels(selected_dropdown_value),
            'y': data_count(selected_dropdown_value, 'Put', 'changeinOpenInterest'),
            'type': 'bar', 'name': 'put-changeinOpenInterest'
        }
        ],
        'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}
    }


@ app.callback(Output('ltp', 'figure'), [Input('scrip', 'value')])
def update_graph(selected_dropdown_value):
    return {
        'data': [{
            'x': labels(selected_dropdown_value),
            'y': data_count(selected_dropdown_value, 'Call', 'lastPrice'),
            'type': 'bar', 'name': 'call-lastPrice'
        },
            {
            'x': labels(selected_dropdown_value),
            'y': data_count(selected_dropdown_value, 'Put', 'lastPrice'),
            'type': 'bar', 'name': 'put-lastPrice'
        }
        ],
        'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}
    }


@ app.callback(Output('probab', 'figure'), [Input('scrip', 'value')])
def update_graph(selected_dropdown_value):
    # inp = output(selected_dropdown_value)
    return {
        'data': [{
            'x': labels(selected_dropdown_value),
            'y': probability(selected_dropdown_value),
            'type': 'scatter', 'name': 'probability'
        }
        ],
        'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}
    }


if __name__ == '__main__':
    app.run_server()
