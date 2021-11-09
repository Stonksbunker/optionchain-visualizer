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


def output(scrip):

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

    # listing all expiry dates
    dates = list(dict.fromkeys(perf['expiryDates']))

    # ther are three differnt expiry options contract
    for m in range(0, 1):
        try:
            expiry = dates[m]
        except:
            break

        labels = []
        maxpain = []

        # listing strikes price in sorted order
        for i in perf['stocks']:
            if i['metadata']['expiryDate'] == expiry:
                labels.append(i['metadata']['strikePrice'])

        labels = list(dict.fromkeys(labels))
        labels.sort()

        # open interest data array maker
        def oi_count(type, value):
            oi = []

            for i in labels:
                temp = len(oi)
                for j in perf['stocks']:
                    if j['metadata']['expiryDate'] == expiry and j['metadata']['optionType'] == type:
                        if str(j['metadata']['strikePrice']) == str(i):
                            if value != 'lastPrice':
                                oi.append(j['marketDeptOrderBook']
                                          ['tradeInfo'][value])
                            else:
                                oi.append(j['metadata'][value])

                if temp == len(oi):
                    oi.append(0)

            return oi

        call = oi_count('Call', 'openInterest')
        put = oi_count('Put', 'openInterest')

        change_call = oi_count('Call', 'changeinOpenInterest')
        change_put = oi_count('Put', 'changeinOpenInterest')

        ltp_call = oi_count('Call', 'lastPrice')
        ltp_put = oi_count('Put', 'lastPrice')

        underlyingValue = perf['underlyingValue']

        strikePrices = perf['strikePrices']
        strikePrices = list(dict.fromkeys(strikePrices))

        # finding nearest strike price for futer calculations
        nearest = []
        l = 0
        for i in strikePrices:
            nearest.append(i - underlyingValue)

        for i in nearest:
            if i < 0:
                nearest[l] = nearest[l] * -1
                l = l + 1

        value = strikePrices[nearest.index(min(nearest))]
        for j in perf['stocks']:
            if j['metadata']['expiryDate'] == expiry and j['metadata']['strikePrice'] == value:
                if j['metadata']['optionType'] == 'Call':
                    iv_call = j['marketDeptOrderBook']['otherInfo']['impliedVolatility']
                if j['metadata']['optionType'] == 'Put':
                    iv_put = j['marketDeptOrderBook']['otherInfo']['impliedVolatility']

        prob = []
        daysexpiry = (datetime.datetime.strptime(expiry, '%d-%b-%Y') -
                      datetime.datetime.strptime(today, '%Y-%m-%d')).days

        for i in labels:
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

        # finding maxpain
        for i in labels:
            max_l = 0

            for k in range(0, labels.index(i) + 1):
                max_l = max_l + (i - labels[k])*call[k]

            for k in range(labels.index(i), len(labels)):
                max_l = max_l + (labels[k] - i)*put[k]

            maxpain.append(max_l)

        minpos = maxpain.index(min(maxpain))

        x = np.arange(len(labels))

        pcr = []
        j = 0
        for i in labels:
            if call[j] == 0:
                pcr.append(1)
            else:
                if put[j]/call[j] > 10:
                    pcr.append(-1)
                else:
                    pcr.append(put[j]/call[j])
            j = j + 1

        return [labels, call, put, change_call, change_put, ltp_call, ltp_put, prob, pcr, maxpain, minpos]


app = dash.Dash('Optionchain', external_stylesheets=[
                'https://codepen.io/chriddyp/pen/bWLwgP.css'])


# bringing data in memory
with open('fno.json') as g:
  fno_scrips = json.load(g)

# fno_scrips = []
# for i in fno_list['data']:
#   fno_scrips.append(i['symbol'])
 

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
        dcc.Tab(label='Tab two', children=[
            dcc.Graph(
                figure={
                    'data': [
                        {'x': [1, 2, 3], 'y': [1, 4, 1],
                            'type': 'bar', 'name': 'SF'},
                        {'x': [1, 2, 3], 'y': [1, 2, 3],
                         'type': 'bar', 'name': u'Montréal'},
                    ]
                }
            )
        ]),
        dcc.Tab(label='Tab three', children=[
            dcc.Graph(
                figure={
                    'data': [
                        {'x': [1, 2, 3], 'y': [2, 4, 3],
                            'type': 'bar', 'name': 'SF'},
                        {'x': [1, 2, 3], 'y': [5, 4, 3],
                         'type': 'bar', 'name': u'Montréal'},
                    ]
                }
            )
        ]),
    ])
], style={'width': '500'})


@ app.callback(Output('callput', 'figure'), [Input('scrip', 'value')])
def update_graph(selected_dropdown_value):
    inp = output(selected_dropdown_value)
    return {
        'data': [{
            'x': inp[0],
            'y': inp[1],
            'type': 'bar', 'name': 'call'
        },
            {
            'x': inp[0],
            'y': inp[2],
            'type': 'bar', 'name': 'put'
        },
            {
            'x': inp[0],
            'y': inp[8],
            'type': 'scatter', 'name': 'pcr'
        }
        ],
        'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}
    }


if __name__ == '__main__':
    app.run_server()
