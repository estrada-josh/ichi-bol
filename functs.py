import pandas as pd
from datetime import date
import numpy as np
import yfinance as yf
import datetime as dt
from pandas_datareader import data as pdr
import requests
from statistics import mean

# Backtest simulates buying and selling based on the if statements within it.
### USE THIS TO TEST STRATEGIES ###
## Returns a list of positive or negative trade results per ticker ##
def backtest(stock):
    #yahoo finance workaround
    yf.pdr_override()

    #holds tickers with score. If ticker is located in other lists it gets added here with amount of times its found
    # pool = {}

    #score to assign to each stock in the pool dictionary
    score = 0

    #start and end of info gathering
    start = dt.datetime(2020,1,1)
    end = date.today()

    #create data frame with stock info and average volume over last 14 days
    df = round(pdr.get_data_yahoo(stock,start,end, progress = False),3)

    ################

    #Calculating RSI

    #create column that tracks difference in price over each day and creates new up or down colums
    # dont need to create columns for this. But they are useful to visualize the values and check work
    # df['Delta'], df['Up'], df['Down']
    delta = df.iloc[:,4].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)

    #variables that contain average value over 14 days of differences in price per day
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()

    #RSI formula and put it in a new RSI column in the dataframe
    rs = ema_up/ema_down
    df['RSI'] = round(100 - (100/(1 + rs)),2)
    df['Ave Vol'] = round(df.iloc[:,5].mean(),2)

    ################

    # New Column for Volume MA
    df['Vol MA'] = round(df.iloc[:,5].ewm(span=20, adjust=False).mean(),3)

    #Create and calculate short term and long term EMA lines

    # list of numbers to use for ema periods
    ema_used = [3,5,8,10,12,15,30,35,40,45,50,60]

    # creates new column for each ema period in the above list
    for per in ema_used:
        ema_str = str(per) + 'EMA'
        df[ema_str] = round(df.iloc[:,4].ewm(span=per, adjust=False).mean(),3)


    score = 0
    pos = 0
    num = 0
    percentchage = []
    buy_sell = []
    # looking up value for each column and checking the lowest ema value and the highest ema value
    for i in df.index:
        crit_min = min(df['3EMA'][i],df['5EMA'][i],df['8EMA'][i],df['10EMA'][i],df['12EMA'][i],df['15EMA'][i])
        crit_max = max(df['30EMA'][i],df['35EMA'][i],df['40EMA'][i],df['45EMA'][i],df['50EMA'][i],df['60EMA'][i])
        short_ema_top = max(df['3EMA'][i],df['5EMA'][i],df['8EMA'][i],df['10EMA'][i],df['12EMA'][i],df['15EMA'][i])
        long_ema_bot = min(df['30EMA'][i],df['35EMA'][i],df['40EMA'][i],df['45EMA'][i],df['50EMA'][i],df['60EMA'][i])
        rsi_val = df['RSI'][i]
        rsi_avg = round(df['RSI'].mean(),2)
        close = df['Adj Close'][i]
        open = df['Open'][i]
        vma = df['Vol MA'][i]
        vol = df['Volume'][i]
        #if short term emas are all above all long term emas, score increase Trending up

        ##### CHANGE THE STATEMENTS BELOW TO MODIFY STRATEGIES #####


        if crit_min > crit_max:
            score = 70

        if score >= 70:
            if close > crit_min:
                score = score + 25
            if close > open:
                score = score + 5
            if close > short_ema_top:
                score = score + 5
            if close < short_ema_top:
                score = score - 5

            if vol > vma:
                score = score + 1
            if rsi_val < 65:
                score = score + 1

        if close < crit_min:
            score = 0

        ##### CHANGE THE STATEMENTS ABOVE TO MODIFY STRATEGIES #####

        #### BELOW: Simulates entering and exiting positions based on score ####

        if score >= 100 and score <= 120:
            if pos == 0:
                bp = open
                pos = 1
                buy_alert = ('Buying ', stock, ' at', bp)
                if num == df['Adj Close'].count() -1:
                    buy_sell.append(stock)

        elif score < 95:
            if pos == 1:
                pos = 0
                sp = close
                sell_alert = ('Selling ', stock, ' at', sp)
                pc = (sp/bp-1)*100
                rounded_pc = str(round(pc, 2))
                percentchage.append(rounded_pc)
                if num == df['Adj Close'].count() - 1:
                    print(sell_alert, i,'Score: ',score,'Return: ',rounded_pc,'%')


        if num == df['Adj Close'].count() and pos == 1:
            pos = 0
            sp = close
            sell_alert = ('Selling at', sp)
            pc = (sp/bp-1)*100
            rounded_pc = str(round(pc, 2))
            percentchage.append(rounded_pc)
            # print(sell_alert, i,'Score: ',score,'Return: ',rounded_pc,'%')

        num = num + 1

    last_score = score

    return percentchage, last_score, close

# clean_file reads a csv and narrows the data down to specific entries based on parameters.
### USE THIS TO SHRINK THE AMOUNT OF TICKERS TO READ THROUGH ###
## Returns a list of unanalyzed tickers ##
def clean_file(file):

    tickers = []
    vol_lim = 2500000
    price_min = 50.00
    price_max = 100.00

    df = pd.read_csv(file, parse_dates = True, index_col=0)
    # for tic_p in df['Last Sale'].index:

    for tic in df['Volume'].index:
        last_sale = (df['Last Sale'][tic])
        ls_int = float(last_sale[1:])
        vol = (df['Volume'][tic])
        if vol > vol_lim and ls_int > price_min and ls_int < price_max:
            tickers.append(tic)

    return tickers

# Collects Ticker Price data and calculates indicators and scores tickers based on criteria
### USE THIS TO CREATE A LIST OF HIGH PERFORMING TICKERS ###
## Returns a list of scored tickers ##
# Note: Will be returning the list of scored tickers w/o the scores in order
# to use the list in backtest seamlessly
def auto_ta(stock):

    #yahoo finance workaround
    yf.pdr_override()

    # Holds tickers with score. If ticker is located in other lists it gets added here with amount of times its found
    # pool = {}
    # tic_pool = []
    #start and end of info gathering
    start = dt.datetime(2020,1,1)
    end = date.today()
    # end = dt.datetime(2021,2,3)

    #create data frame with stock info and average volume over last 14 days
    df = round(pdr.get_data_yahoo(stock,start,end, progress = False),3)

    ################

    #Calculating RSI

    #create column that tracks difference in price over each day and creates new up or down colums
    # dont need to create columns for this. But they are useful to visualize the values and check work
    # df['Delta'], df['Up'], df['Down']
    delta = df.iloc[:,4].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)

    #variables that contain average value over 14 days of differences in price per day
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()

    #RSI formula and put it in a new RSI column in the dataframe
    rs = ema_up/ema_down
    df['RSI'] = round(100 - (100/(1 + rs)),2)

    # New column that contains average volume
    df['Ave Vol'] = round(df.iloc[:,5].mean(),2)

    # New Column for Volume MA
    df['Vol MA'] = round(df.iloc[:,5].ewm(span=20, adjust=False).mean(),3)

    ################

    #Create and calculate short term and long term EMA lines

    # list of numbers to use for ema periods
    ema_used = [3,5,8,10,12,15,30,35,40,45,50,60]

    # creates new column for each ema period in the above list
    for per in ema_used:
        ema_str = str(per) + 'EMA'
        df[ema_str] = round(df.iloc[:,4].ewm(span=per, adjust=False).mean(),3)

    # Set variables for scoring and backtesting
    out_stock = None
    score = 0
    pos = 0
    num = 0
    percentchage = []
    buy = []


    # looking up value for each column and checking the lowest ema value and the highest ema value
    for i in df.index:
        crit_min = min(df['3EMA'][i],df['5EMA'][i],df['8EMA'][i],df['10EMA'][i],df['12EMA'][i],df['15EMA'][i])
        crit_max = max(df['30EMA'][i],df['35EMA'][i],df['40EMA'][i],df['45EMA'][i],df['50EMA'][i],df['60EMA'][i])
        short_ema_top = max(df['3EMA'][i],df['5EMA'][i],df['8EMA'][i],df['10EMA'][i],df['12EMA'][i],df['15EMA'][i])
        long_ema_bot = min(df['30EMA'][i],df['35EMA'][i],df['40EMA'][i],df['45EMA'][i],df['50EMA'][i],df['60EMA'][i])
        rsi_val = (df['RSI'][i])
        rsi_avg = round(df['RSI'].mean(),2)
        close = df['Adj Close'][i]
        open = df['Open'][i]
        vma = df['Vol MA'][i]
        vol = df['Volume'][i]

        ##### CHANGE THE STATEMENTS BELOW TO MODIFY STRATEGIES #####

        if crit_min > crit_max:
            score = 70

        if score >= 70:
            if close > crit_min:
                score = score + 25
            if close > open:
                score = score + 5
            if close > short_ema_top:
                score = score + 5
            if close < short_ema_top:
                score = score - 5

            if vol > vma:
                score = score + 1
            if rsi_val < 65:
                score = score + 1

        if close < crit_min:
            score = 0

        ##### CHANGE THE STATEMENTS ABOVE TO MODIFY STRATEGIES #####
        #### BELOW: Simulates entering and exiting positions based on score ####
        if score >= 100 and score <= 120:
            if pos == 0:
                bp = close
                pos = 1
                buy_alert = ('Buy ', stock, ' at', bp)
                if num == df['Adj Close'].count() -1:
                    out_stock = stock
                    # buy.append(stock)
                    print('\n',buy_alert, i,'Score: ', score,'\n')


        elif score < 100:
            if pos == 1:
                pos = 0
                sp = close
                sell_alert = ('Sell ', stock, ' at', sp)
                pc = (sp/bp-1)*100
                rounded_pc = str(round(pc, 2))
                percentchage.append(rounded_pc)
                if num == df['Adj Close'].count() - 1:
                    print('\n',sell_alert, i,'Score: ',score,'Return: ',rounded_pc,'%\n')

        num = num + 1

        # ^^^ ### ### #### ### ### ### ### ### ^^^ #

    #Format the dictionary to be more readable and return the formatted dictionary of tickers with their scores
    # pool_f = {}

    # if score >= 110 and score <= 120:
        # pool[stock] = pool.get(stock,score)
        # tic_pool.append(stock)
        # pool_f = '\n'.join("{}: {}".format(k, v) for k, v in pool.items())
        # out_stock = stock
    # if pool_f != None:
        # return pool_f
        # return tic_pool

    return out_stock, score, percentchage
