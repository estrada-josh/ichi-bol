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
import smtplib

# Lists to be populated by later operations
tickers = []
alerts_list = []
holding_symbols = []

# files = ['test.csv']
files = ['/Users/josh/desktop/dev/python/local-projects/bol-ichi-ta/amex.csv','/Users/josh/desktop/dev/python/local-projects/bol-ichi-ta/nasdaq.csv','/Users/josh/desktop/dev/python/local-projects/bol-ichi-ta/nyse.csv']

# Looks through the files listed in 'files'
# 'filters' function returns a narrowed down list of tickers
#  the tickers are then added to the empty list created above

for file in files:
    tick_list = funcs.filters(file)
    for x in tick_list:
        tickers.append(x)

print('\n \n ########### STARTING ALGO TA ########### \n \n')
# Runs list of tickers through each function
# Prints Dataframes and trade results
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
    simlen = len(sim[0])
    simtot = 0
    for i in sim[0]:
        simtot = i + simtot

    price_sum = score[['Open','Close','Conv Line','Upper','Score']]

    # Only shows tickers that had more than one buy or sell
    avg = 0
    if simlen > 0 and simtot > 0:
        avg = round((simtot / simlen),2)

    # prints results for ticker
    if avg >= 10:
        if len(sim[0]) >= 0:
            print()
            print(ticker)
            print(price_sum.tail(10))
            print('_________________________________________________', '\n')
            print(len(sim[0]),'trade Sim Results (%): ',sim[0])
            print('Average return %: ',avg)
            print()
            if len(alerts) > 0:
                alerts_list.append(alerts)
            if sim[2] != None:
                holding_symbols.append(sim[2])
            print('TRADES: \n')
            for row in sim[3]:
                print(row, sim[3][row], '\n')
            if sim[1] != None:
                print(sim[1], '\n')
            print('#################################################')



# Prints every buy and sell alert for the current day
print('### ALERTS ###\n')
for alert in alerts_list:
    print(alert, '\n')
print('Currently holding',len(holding_symbols), 'stocks:', holding_symbols, '\n')

# Email alert setup
sender_email = 'your email here'
rec_email = 'youre recipients here'
### DO NOT PUSH TO GIT WITH THIS ####
password = 'your pw'
### DO NOT PUSH TO GIT WITH THIS ####
message = 'Subject: {}\n\n{}'.format('Algo Alert!', ('\n'+ str(alerts_list)))

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(sender_email, password)
server.sendmail(sender_email, rec_email, message)
