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
from flask import Flask

tickers = []
alerts_list = []
# files = ['test.csv']
files = ['amex.csv','nasdaq.csv','nyse.csv']

for file in files:
    tick_list = funcs.filters(file)
    for x in tick_list:
        tickers.append(x)

for ticker in tickers:

    df = funcs.data(ticker)
    score = funcs.scores(df)
    alerts = funcs.alerts(score)
    sim = funcs.sim(score)

    simlen = len(sim)
    simtot = 0
    for i in sim:
        simtot = i + simtot

    avg = round((simtot / simlen),2)

    if avg >= 10:
        print()
        print(ticker)
        print(score.tail(3))
        print()
        print('Trade Sim Results (%): ',sim)
        print('Average return %: ',avg)
        print()
        if len(alerts) > 0:
            alerts_list.append(alerts)

print('### ALERTS ###\n')
for alert in alerts_list:
    print(alert)
