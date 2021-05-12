# Main program that runs the analysis

import pandas as pd
from datetime import date
import numpy as np
import yfinance as yf
import datetime as dt
from datetime import timedelta
from pandas_datareader import data as pdr
import requests
from statistics import mean
import funcs

# Lists to be populated by later operations
tickers = []
alerts_list = []

# files = ['test.csv']
files = ['amex.csv','nasdaq.csv','nyse.csv']

# Looks through the files listed in 'files'
# 'filters' function returns a narrowed down list of tickers
#  the tickers are then added to the empty list created above
for file in files:
    tick_list = funcs.filters(file)
    for x in tick_list:
        tickers.append(x)

# Runs list of tickers through each function
for ticker in tickers:

    # Pulls price data from the web and creates dataframe
    df = funcs.data(ticker)

    # scores each tickers current performance
    score = funcs.scores(df)

    # decides when to buy or sell based on performance
    alerts = funcs.alerts(score)

    # simulates buying and selling for the past 60 days based on performance score
    # returns a list of buy and sell results
    sim = funcs.sim(score)

    # Calculate average results
    simlen = len(sim)
    simtot = 0
    for i in sim:
        simtot = i + simtot

    # Only shows tickers that had more than one buy or sell
    if simlen > 0 and simtot > 0:
        avg = round((simtot / simlen),2)

        # prints results for ticker
        if avg >= 5:
            print()
            print(ticker)
            print(score.tail(3))
            print()
            print('Trade Sim Results (%): ',sim)
            print('Average return %: ',avg)
            print()
            if len(alerts) > 0:
                alerts_list.append(alerts)

# Prints every buy and sell alert for the current day
print('### ALERTS ###\n')
for alert in alerts_list:
    print(alert)
