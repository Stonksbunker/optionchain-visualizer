import os
import datetime
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests
import numpy as np
import math
import scipy.integrate as integrate
import multiprocessing

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

# start of requesting and storing data
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

# list of all scrips
fno_list_url = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"
resp = requests.get(url=nse_url, headers=request_headers)
if resp.ok:
  req_cookies = dict(
    nsit=resp.cookies['nsit'], nseappid=resp.cookies['nseappid'], ak_bmsc=resp.cookies['ak_bmsc'])
  response = requests.get(
    url=fno_list_url, headers=request_headers, cookies=req_cookies).json()
  with open('fno_list.json', 'w') as f:
    json.dump(response, f)

# bringing data in memory
with open('fno.json') as g:
  fno_scrips = json.load(g)

# fno_scrips = []
# for i in fno_list['data']:
#   fno_scrips.append(i['symbol'])


# requesting data of all scrips
for scrip in fno_scrips:
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
  print("response OK for ", scrip)
  print("Plot generated")

# driver function
def output(scrip):

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
                oi.append(j['marketDeptOrderBook']['tradeInfo'][value])
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
    daysexpiry = (datetime.datetime.strptime(expiry, '%d-%b-%Y') - datetime.datetime.strptime(today, '%Y-%m-%d')).days

    for i in labels:
      # STRIKE<VALUE WIN PROB => NORMSDIST(LN(STRIKEPRICE/VALUE)/CALLIV*SQRT(DAYSTOEXPIRATION/365))
      # normsdist = (1/2pi)^2 * e^(-(z^2)/2)
      if i < value and i > 0:
        try:
          normsdist = math.log(i/underlyingValue) / ((iv_call/100)*math.sqrt(daysexpiry/365))
          result = integrate.quad(lambda q: ((1/math.sqrt(2 * math.pi))*((math.e)**(q**2/-2.0))), -np.inf, normsdist)
          prob.append(100 - result[0]*100)
        except:
          prob.append(0)
      elif i > value and i > 0:
        try:
          normsdist = math.log(i/underlyingValue) / ((iv_put/100)*math.sqrt(daysexpiry/365))
          result = integrate.quad(lambda q: ((1/math.sqrt(2 * math.pi))*((math.e)**(q**2/-2.0))), -np.inf, normsdist)
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

    # plotting starts
    width = 0.5

    fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(nrows=5, ncols=1)
    fig.set_figheight(25)
    fig.set_figwidth(30)

    rects1 = ax1.bar(x - width/2, call, width, label='call')
    rects2 = ax1.bar(x + width/2, put, width, label='put')

    rects3 = ax3.bar(x - width/2, change_call, width, label='change_call')
    rects4 = ax3.bar(x + width/2, change_put, width, label='change_put')

    rects5 = ax4.bar(x - width/2, ltp_call, width, label='change_call')
    rects6 = ax4.bar(x + width/2, ltp_put, width, label='change_put')

    title = "".join(['Underlying Value - ', str(perf['underlyingValue']), ' - - Lot Size - ', str(perf['stocks'][0]['marketDeptOrderBook']['tradeInfo']['marketLot'])])

    props = {
      'title': title,
      'xticks': x,
      'xticklabels': labels,
    }
    ax1.set(**props)
    ax2.set(**props)
    ax3.set(**props)
    ax4.set(**props)
    ax5.set(**props)
    ax1.tick_params(labelsize=8, rotation=90)
    ax2.tick_params(labelsize=8, rotation=90)
    ax3.tick_params(labelsize=8, rotation=90)
    ax4.tick_params(labelsize=8, rotation=90)
    ax5.tick_params(labelsize=8, rotation=90)

    def autolabel(rects, axis):
      for rect in rects:
        height = rect.get_height()
        axis.annotate('{}'.format(height),
                      xy=(rect.get_x() + rect.get_width() / 2, height),
                      xytext=(0, 3),
                      textcoords="offset points",
                      ha='center', va='bottom', fontsize=6)

    autolabel(rects1, ax1)
    autolabel(rects2, ax1)

    autolabel(rects3, ax3)
    autolabel(rects4, ax3)

    autolabel(rects5, ax4)
    autolabel(rects6, ax4)

    def lines(lineinfo):
      for i in lineinfo:
        for j in i['xline']:
          i['axis'].axvline(x=j, color='green')
        for j in i['hline']:
          i['axis'].axhline(y=j, color='red')

    lines([
      {'axis': ax1, 'xline': {minpos, labels.index(value)}, 'hline': {}},
      {'axis': ax2, 'xline': {minpos, labels.index(value)}, 'hline': {0}},
      {'axis': ax3, 'xline': {minpos, labels.index(value)}, 'hline': {}},
      {'axis': ax4, 'xline': {minpos, labels.index(value)}, 'hline': {}},
      {'axis': ax5, 'xline': {minpos, labels.index(value)}, 'hline': {25, 50, 75}}
    ])

    ax2.plot(x, pcr)
    ax5.plot(x, prob)

    plt.savefig('./data/outputs/'+ today +'output/' + scrip + expiry + '-oi-' + today + '.png')

    plt.clf()
    plt.close('all')


if __name__ == '__main__':
  pool = multiprocessing.Pool()
  inputs = fno_scrips
  outputs = pool.map(output, inputs)
