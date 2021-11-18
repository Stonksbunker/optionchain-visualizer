---
title: "**YASP: Yet Another Stock Predictor**"
papersize: a4
numbersections: true
author: 
- "**Umang Bhalla**"
autoEqnLabels: true
fontsize: 8pt
mainfont: TeX Gyre Pag
geometry:
- top=30mm
- left=12mm
- right=12mm
- bottom=35mm
header-includes: |
	\usepackage{float}
	\let\origfigure\figure
	\let\endorigfigure\endfigure
	\renewenvironment{figure}[1][2] {
		\expandafter\origfigure\expandafter[H]
	}{
		\endorigfigure
	}
	\usepackage{multicol}
	\newcommand{\hideFromPandoc}[1]{#1}
	\hideFromPandoc{
		\let\Begin\begin
		\let\End\end
	}
date: November 17, 2021
keywords: [nothing, nothingness]
output: pdf_document
abstract:
	In this research paper we dive deep into webscrapping , flask Server setup and Optionchain stocks visualisation 
---
<!-- # Appendix {-} -->
\tableofcontents
\listoftables
\listoflistings
\newpage


\Begin{multicols}{2}
# Introduction 
**Optionchain visualiser** is a collection of *multiple* technologies, like **python programming language**, **bash scripting**, **json** as database, **flask** as software based server , **Raspberry pi 4b** as hardware server and **arch linux** as operating system [^1].  

Using web-scraping we extract data from NSE [^2] which gets saved in database (as json file) then using matplotlib in first varient and dash(component in plotty [^plotty]) we generate static pngs and interactive graphs.

classoption:
- twocolumn

## Mechanism and how it works.
Both **varients**[^v] of this project scrape **NSE** [^2] to collect relevant data about user provieded stocks or all the public stocks listed on the exchange.
After this is done, the collected json data is add to *data* subdirectory and named as *stockname*-fno.json


## Methods of Data Scraping used

\End{multicols}

\newpage

\Begin{multicols}{2}

# Probability by normal distribution

Strike price : current price of stock

Implied volatility is not directly observable, so it needs to be solved using the five other inputs of the Black-Scholes model, which are:
- The market price of the option.
- The underlying stock price.
- The strike price.
- The time to expiration.
- The risk-free interest rate.

Implied volatility is calculated by taking the market price of the option, entering it into the Black-Scholes formula, and back-solving for the value of the volatility. But there are various approaches to calculating implied volatility. One simple approach is to use an iterative search, or trial and error, to find the value of implied volatility.
Iv calculation done by nse


Call iv -> call implied volatility (given by nse)
put iv -> put option implied volatility (given by nse)
Days of expiry -> expiryDate - today

\End{multicols}

> Strike value win probability =


> NORMSDIST(LN(STRIKEPRICE/VALUE)/CALLIV\*SQRT(DAYSTOEXPIRATION/365))

> NORMSDIST = (0.5\*pi)^2^ \* e^(-(z²)/2)^

```{.python .numberLines}
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
#STRIKE<VALUE WIN PROB => NORMSDIST(LN(STRIKEPRICE/VALUE)/CALLIV*SQRT(DAYSTOEXPIRATION/365))
#normsdist = (1/2pi)^2 * e^(-(z^2)/2)
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
```

\Begin{multicols}{2}

### What nse use for IV calculation and we get by api

Calculation of theoretical base price of contracts as per Black –Scholes formula:
The options price for a Call option shall be computed as follows:

C = S * N (d1) – X * e ^ (- rt )\* N (d2)


and the price for a Put option is :


P = X * e ^ (- rt ) * N (-d2) – S * N (-d1)


where :


d1 = ln (S / X) + (r + s ^ 2 / 2) * t


s * vt


d2 = ln (S / X) + (r – s 2 / 2) * t


s * vt


= d1 - s * vt


and
C = price of a Call option


P = price of a Put option


S = price of the underlying asset


X = Strike price of the option


r = rate of interest (Rate of interest shall be the relevant MIBOR rate for the day)


t = time to expiration


s = volatility (Volatility shall be the higher of the underlying volatility or the the near month futures contact volatility on the relevant day.)


N represents a standard normal distribution with mean = 0 and standard deviation = 1, and ln represents the natural logarithm of a number. Natural logarithms are based on the constant e (2.71828182845904).





## Different varients of the project {#sec:varients}
### User input based
This varient primarily relies on user to decide stock about which he/she has to scrape information. Using the run [^prerun] script provided in the repository user call the fzf [^fzf] prompt. 
In the fzf [^fzf] prompt user is supposed to write name of the stock they want to search, the search usses fuzzy algorithm [^fuzzy] , hence if we write *SBI* in the search prompt,  **SBIN** , **SBILIFE** , **SBICARD** gets displayed as results ; then user can press tab to select the symbol [^symbols] on the promt and press it again to select the enxt prompt or search for other symbol [^symbols] to add the array that will be fed to python script to start the scrape.


\End{multicols}


```{.bash .numberLines}
#!/bin/bash
rm -rf data
mkdir -p data
fno_list_Arr=$(cat fno_main.json | jq ".[]" | jq ".[].symbol" | fzf --reverse -m -i --height=80%);
arr=($fno_list_Arr)


final="["
for i in "${arr[@]}"
do
  final=$final"{\"label\": $i, \"value\": $i} ,"
done

final=${final::-1}"]"
 
echo $final
echo $final > fno.json

python3 optionchain.py
```

\Begin{multicols}{2}

### Server based (Flask)

*  *  *  *

## Difference between both varients.

# Propose work

# Block diagram

# Data Set and visualization 
like excel sheet

# Result and Implementation
minimum requirement, setup

# Conclusion and Future

# References


\End{multicols}


[^1]: arch linux is used as it provides arch user repository which hosts a lot of commandline tools used in this project
[^2]: National Stock Exchange www.nseindia.com
[^v]: see [@sec:varients]
[^plotty]: lllllllllllllll
[^prerun]: sssssssssss
[^fzf]: oooooooooooo
[^symbols]: jjjjjjjjjjjj
[^fuzzy]: ffffffffffff
