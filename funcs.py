import pandas as pd
from datetime import date
import numpy as np
import yfinance as yf
import datetime as dt
from datetime import timedelta
from pandas_datareader import data as pdr
import requests
from statistics import mean

# Returns list of tickers
def filters(file):
    tickers = []
    vol_lim = 500000
    price_min = 5.00
    price_max = 12.00

    df = pd.read_csv(file, parse_dates = True, index_col=0)
    # for tic_p in df['Last Sale'].index:

    for tic in df['Volume'].index:
        last_sale = (df['Last Sale'][tic])
        ls_int = float(last_sale[1:])
        vol = (df['Volume'][tic])
        if vol > vol_lim and ls_int > price_min and ls_int < price_max:
            tickers.append(tic)

    return tickers

# Returns dataframe with price data using ta indicators
def data(stock):

    #yahoo finance workaround
    yf.pdr_override()

    #create data frame with stock info
    df = yf.download(  # or pdr.get_data_yahoo(...
        # tickers list or string as well
        tickers = stock,

        # use "period" instead of start/end
        # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        # (optional, default is '1mo')
        period = "ytd",

        # fetch data by interval (including intraday if period < 60 days)
        # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        # (optional, default is '1d')
        interval = "1h",

        # adjust all OHLC automatically
        # (optional, default is False)
        auto_adjust = False,

        # download pre/post regular market hours data
        # (optional, default is False)
        prepost = False,

        progress = False
    )

    # Add column with Ticker for alerting purposes
    df['Symbol'] = stock

    # RSI formula and put it in a new RSI column in the dataframe
    # variables that contain average value over 14 days of differences in price per day
    # ema_up = up.ewm(com=13, adjust=False).mean()
    # ema_down = down.ewm(com=13, adjust=False).mean()
    # rs = ema_up/ema_down
    # df['RSI'] = round(100 - (100/(1 + rs)),2)

    # Adding Bollinger Bands
    df['MA20'] = df['Adj Close'].rolling(window = 20).mean()
    df['20dSTD'] = df['Adj Close'].rolling(window = 20).std()

    df['Upper'] = df['MA20'] + (df['20dSTD'] * 2)
    df['Lower'] = df['MA20'] - (df['20dSTD'] * 2)

    # Adding MAs
    df['MA60'] = df['Adj Close'].rolling(window = 60).mean()
    df['MA120'] = df['Adj Close'].rolling(window = 120).mean()

    # Adding Vol MA over 60 periods
    df['MA Vol'] = df['Volume'].rolling(window = 60).mean()

    # Adding Ichi Cloud

    # Conversion Line (blue line)
    high_8 = df['High'].rolling(window= 8).max()
    low_8 = df['Low'].rolling(window= 8).min()
    df['Conv Line'] = (high_8 + low_8) /2

    # Base Line (Red line )
    high_22 = df['High'].rolling(window= 22).max()
    low_22 = df['Low'].rolling(window= 22).min()
    df['Base Line'] = (high_22 + low_22) /2

    # Span A (Green Cloud Line)
    df['Span A'] = ((df['Conv Line'] + df['Base Line']) / 2).shift(26)

    # Span B (Red Cloud Line)
    high_44 = df['High'].rolling(window= 44).max()
    low_44 = df['Low'].rolling(window= 44).min()
    df['Span B'] = ((high_44 + low_44) /2).shift(26)

    # Lagging Span (Dark Green Line)
    # df['Lag Span'] = df['Close'].shift(-26)

    # print(stock + ' data frame complete')
    return df

# Reads through a dataframe and scores each interval based on criteria
# Returns new dataframe with scores column for simming trades
def scores(df):

    scores = []
    score = 0

    for i in df.index:


        # Standard Price info
        high = df['High'][i]
        low = df['Low'][i]
        close = df['Adj Close'][i]
        open = df['Open'][i]
        vol_avg = df['MA Vol'][i]
        vol = df['Volume'][i]

        # RSI
        # rsi = df['RSI'][i]

        # Bollinger Band identifiers
        bol_top = df['Upper'][i]
        bol_mid = df['MA20'][i]
        bol_bot = df['Lower'][i]
        bol_vla = df['20dSTD'][i]

        # MA 60 and 120
        ma60 = df['MA60'][i]
        ma120 = df['MA120'][i]

        # Ichimoku Cloud identifiers
        conv = df['Conv Line'][i]
        base = df['Base Line'][i]
        span_a = df['Span A'][i]
        span_b = df['Span B'][i]
        # lag_span = df['Lag Span'].iloc[[-27]]

        # Lag Close and lagging Span a & b to be used with lag_span
        # lag_close = df['Adj Close'].iloc[[-27]]
        # lag_span_a = df['Span A'].iloc[[-27]]
        # lag_span_b = df['Span B'].iloc[[-27]]

        ############################################
        # Score reset to read summary df more easily

        # Trade conditions
        if score == 1300:
            score = 1

        # Buy conditions
        if conv < bol_mid and open < conv:
            if close > conv and close > bol_mid and vol > vol_avg and close > base:
                score = 1300


        if score == 1600:
            score = 0

        # Selling conditions
        if open > bol_top and open > conv and open > base:
            score = 1500

        if score == 1500:
            if close < bol_top:
                score = 1600

        scores.append(score)
        ############################################


    # Add new column to dataframe: Score
    df['Score'] = scores

    return df

# Reads through dataframe from scores function
# Simulates trading on historical price data
# Returns printed report of P/L
# Returns weather or not the stock is currently bought
def sim(df):

    # Sets todays date and sets a purchase date variable
    today = dt.date.today()
    pur_date = None
    sel_date = None
    pur_info = None
    sel_info = None

    # Sets switch for bought or not bought positions
    bought = 0

    # Buy and sell levels
    buy_score = 1300
    sell_score = 1600

    # Sets empty list to hold percent change per trade and show trades
    percents = []
    trades = {}

    for i in df.index:

        symbol = df['Symbol'][i]
        price = round((df['Close'][i]), 2)
        score = df['Score'][i]

        # Alert to buy if score is 300
        if score == buy_score:
            if bought == 0:
                bought = 1

                # purchase info
                bp = price
                pur_date = i.date()
                i_str = str(i)
                time = i_str[11:16]

                # purchase info string and add to trades dic
                pur_info = ('Bought at $' + str(bp) + ' ' + str(pur_date) + ' ' + time + ' ##')

        # If symbol is already bought and score is 600, alert to sell
        if score == sell_score:
            if bought == 1:
                bought = 0

                # sell price
                sp = price

                # sell info
                sel_date = i.date()
                i_str = str(i)
                time = i_str[11:16]

                # sell info string and add to trades dic
                sel_info = ('Sold at $' + str(sp) + ' ' + str(sel_date) + ' ' + time)

                # Percent change (pc) calculation
                pc = round((sp/bp-1)*100,2)
                percents.append(pc)

                trades[pur_info] = sel_info



        # insert into trade dict
        # if pur_info != None and sel_info != None:

        # # Close positions if today
        # if i == today and bought == 1:
        #     # sell price
        #     sp = price
        #     # Percent change (pc) calculation
        #     pc = round((sp/bp-1)*100,2)
        #     percents.append(pc)

    # sets up variable holding to return if the stock is currently bought
    holding = None
    holding_symbol = None

    # If stock is bought, remember when it was bought and at what price
    if bought == 1:
        holding = ('Currently holding; ' + pur_info)
        holding_symbol = symbol

    return percents, holding, holding_symbol, trades

# Reads through dataframe from scores function
# Returns alerts if alerted on same day
def alerts(df):

    # Sets switch for bought or not bought positions
    bought = 0

    # Buy and sell levels
    buy_score = 1300
    sell_score = 1600

    # Sets empty list to hold alerts
    alerts = []

    # Sets todays date
    today = dt.date.today()


    for i in df.index:

        dates = i.date()
        i_str = str(i)
        time = i_str[11:16]

        symbol = df['Symbol'][i]
        price = round((df['Close'][i]), 2)
        score = df['Score'][i]

        # Alert to buy if score is 300
        if score == buy_score:
            if bought == 0:
                bought = 1
                alert = (str(symbol) + ': ### Buy ### @ $' + str(price) + ' ' + str(dates) + ' ## ' + time)
                if dates == today:
                    alerts.append(alert)

        # If symbol is already bought and score is 600, alert to sell
        elif score == sell_score:
            if bought == 1:
                bought = 0
                alert = (str(symbol) + ' ### Sell ### @ '+str(price) + ' @ ' + str(dates) + ' ## ' + time)
                if dates == today:
                    alerts.append(alert)



    return alerts
