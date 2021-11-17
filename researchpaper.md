---
title: "**Openchain visualiser**"
papersize: a4
numbersections: true
author: 
- "**Umang Bhalla**"
- "**kshgrk**"
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
date: November 17, 2021
keywords: [nothing, nothingness]
classoption:
- twocolumn
output: pdf_document
abstract:
	In this research paper we dive deep into webscrapping , flask Server setup and openchain stocks visualisation 
---
<!-- # Appendix {-} -->
\tableofcontents
\listoftables
\listoflistings
\newpage

# {-}

\newpage
# Introduction 
**Openchain visualiser** is a collection of *multiple* technologies, like **python programming language**, **bash scripting**, **json** as database, **flask** as software based server , **Raspberry pi 4b** as hardware server and **arch linux** as operating system [^1].  

Using web-scraping we extract data from NSE [^2] which gets saved in database (as json file) then using matplotlib in first varient and dash(component in plotty) we generate static pngs and interactive graphs.


## Mechanism and how it works.
Both **varients**[^v] of this project scrape **NSE** [^2] to collect relevant data about user provieded stocks or all the public stocks listed on the exchange.
After this is done, the collected json data is add to *data* subdirectory and named as *stockname*-fno.json


## Methods of Data Scraping used

## Different varients of the project {#sec:varients}
### User input based
### Server based (Flask)

## Difference between both varients.


# Propose work
what we have done,diagram and block diagram
# Block diagram

# Data set used
like excel sheet

# Result and Implementation
minimum requirement, setup

# Conclusion and Future



[^1]: arch linux is used as it provides arch user repository which hosts a lot of commandline tools used in this project
[^2]: National Stock Exchange www.nseindia.com
[^v]: see [@sec:varients]
