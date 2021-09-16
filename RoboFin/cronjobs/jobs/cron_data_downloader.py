import requests
import time
import pandas as pd
import numpy as np
import sys
from .common import etfs, crypto, yahoo_etfs
import yaml
from django.apps import apps
from io import StringIO

def save_to_db(name, df):
    asset = apps.get_model('portfolio', 'Asset')

    # Create if not exists, else update with new data
    asset.objects.update_or_create(
        name=name,
        defaults = {'historical_prices': df.to_csv(index=False)}
    )

def cash_ticker():
    # Create CASH ticker based on some other asset.
    asset = apps.get_model('portfolio', 'Asset')
    existing_asset = asset.objects.get(name="AGG")

    df = pd.read_csv(StringIO(existing_asset.historical_prices))
    df[['open', 'high', 'low', 'close', 'adjusted_close', 'volume', 'split_coefficient']] = 1
    df['dividend_amount'] = 0. 

    save_to_db('CASH', df)

def get_alphavantage_key():
    with open("/Users/andraz/secrets/secrets.yaml", 'r') as stream:
        try:
            secrets = yaml.safe_load(stream)
            return secrets["AlphaVantageKey"]
        except yaml.YAMLError as exc:
            print(exc)
            return "Failed"
            

def yahoo_download(epoch_to, symbol):
    """
        Downloads data from Yahoo Finance and returns Pandas DataFrame2
    """

    # Using all of the available historical data for this symbol
    epoch_from = "1"
    
    url = "https://query1.finance.yahoo.com/v7/finance/download/"\
            + symbol + "?period1="+ epoch_from +"&period2="+ epoch_to +"&interval=1d"\
            "&events=history&includeAdjustedClose=true"

    df = pd.read_csv(url)


    # Add dividend and split coefficient data for consistency (but we do not use them as we have adjusted close prices)
    df['dividend_amount'] = 0.
    df['split_coefficient'] = 1

    # Rename columns
    df = df.rename(columns={'Date': 'timestamp', 'Open': 'open', 'High': 'high',
        'Low': 'low', 'Close': 'close', 'Adj Close': 'adjusted_close',
        'Volume': 'volume'})
    
    # Reverse, to be consistent with etf (first element is latest)
    df = df.iloc[::-1]

    return df

def coindesk_download(epoch_to):
    """
        CoinDesk only has API for Bitcoin (BTC)
    """

    df = pd.read_json("https://api.coindesk.com/v1/bpi/historical/close.json?start=2010-07-17&end="+time.strftime("%Y-%m-%d", time.gmtime(epoch_to))+"")
    df = df.reset_index()
    df.drop(columns=['disclaimer', 'time'], inplace=True)
    
    df = df.rename(columns={'bpi': 'adjusted_close', 'index': 'timestamp'})
    df = df.dropna()

    # Reverse dataframe, so we go from new to old date
    df = df.iloc[::-1]

    return df


def run():
    apikey = get_alphavantage_key()
    # ETFs are captured through AlphaVantage. Crypto lacks older data on AlphaVantage.
    for ticker in etfs:
        uri = """https://www.alphavantage.co/query?
        function=TIME_SERIES_DAILY_adjusted&
        symbol={ticker}&outputsize=full&datatype=csv&
        apikey={key}""".format(ticker=ticker, key=apikey)
        uri = uri.replace(" ", "").replace("\n", "")
        print(uri)

        response = pd.read_csv(uri)
        save_to_db(ticker, response)
        time.sleep(10)

    # # Create the CASH asset
    cash_ticker()

    # Crypto is downloaded via Yahoo
    # No need to worry about splits & dividends - we use adjusted prices
    epoch_now = time.time()
    string_epoch = str(int(epoch_now))
    for ticker in crypto:
        if ticker == 'BTC':
            df = coindesk_download(epoch_now)
        else:
            df = yahoo_download(string_epoch, ticker+"-USD")

        save_to_db(ticker, df)
        print(ticker)
        time.sleep(5)

    # Some tickers have more data in Yahoo
    for ticker in yahoo_etfs:
        df = yahoo_download(string_epoch, ticker)

        save_to_db(ticker, df)
        time.sleep(5)
        print(ticker)