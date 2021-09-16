import pandas as pd
import empyrical as emp
from datetime import datetime, timedelta
import numpy as np
import empyrical as emp
import sys
from empyrical.utils import nanmean
from enum import Enum
from django.apps import apps
from io import StringIO

class Event:
    def __init__(self, title, date_from, date_to):
        self.title = title
        self.date_from = date_from
        self.date_to = date_to

class TacticalMethod(str, Enum):
    sma_20='Simple Moving Average 20 days'
    bollinger_bands='Bollinger bands on SMA20'
    macd="Moving Average Convergence/Divergence 12,26 (fast, slow)"
    rsi="Relative strength index (last 14 days)"
    all='Use all available tactical method and make a move if at least half suggest it'


events = {
    "covid": Event("Covid 2020", pd.to_datetime("2020-02-06 00:00:00"), pd.to_datetime("2020-08-19 00:00:00")),
    "housing": Event("Housing Crash 2008", pd.to_datetime("2007-07-16 00:00:00"), pd.to_datetime("2013-04-04 00:00:00")),
    "dotcom": Event("Dotcom Bubble 2000", pd.to_datetime("2000-03-24 00:00:00"), pd.to_datetime("2007-06-04 00:00:00")),
    "cryptocrash": Event("Crypto Crash 2018", pd.to_datetime("2017-12-10 00:00:00"), pd.to_datetime("2020-12-10 00:00:00")),
    "2015selloff": Event("Selloff 2015", pd.to_datetime("2015-07-20 00:00:00"), pd.to_datetime("2016-07-20 00:00:00")),
    "2017bull": Event("Bull Market 2017", pd.to_datetime("2016-11-04 00:00:00"), pd.to_datetime("2017-12-04 00:00:00")),
    "3yr": Event("Last 3 Years", pd.to_datetime(datetime.now().date() - timedelta(days=3*365)),
        pd.to_datetime(datetime.now().date())),
    "5yr": Event("Last 5 Years", pd.to_datetime(datetime.now().date() - timedelta(days=5*365)),
        pd.to_datetime(datetime.now().date())),
    "10yr": Event("Last 10 Years", pd.to_datetime(datetime.now().date() - timedelta(days=10*365)), 
        pd.to_datetime(datetime.now().date()))
}

tickers = ["AGG", "TAN", "ICLN", "ITA", "XLK", "XLF", "XLV", "XLY",
    "XLI", "XLE", "XLP", "IYZ", "XLU", "XLB",  "IGOV",
    "GLD", "PALL","EWG", "QQQ", "SPY", "VNQ", "BTC", "ETH", "XRP", "CASH"]

# Top 5 cryptocurrencies
crypto = ["BTC", "ETH", "XRP", "ADA", "BNB"]

yahoo_etfs = ["GSG", "IJS", "SHY", "TLT", "IEI", "VTI" ]

all_tickers_sorted = ["AGG", "SHY", "TLT", "IEI", "IGOV", "GLD", "PALL", "GSG",
    "IJS", "TAN", "ICLN", "ITA", "XLK", "XLF", "XLV", "XLY",
    "XLI", "XLE", "XLP", "IYZ", "XLU", "XLB",
    "EWG", "QQQ", "SPY", "VTI", "VNQ",  "BTC", "ETH", "XRP", "ADA", "BNB"]

etfs = [ticker for ticker in tickers if ticker not in crypto and ticker not in ["CASH"]]

# Views for Black-Litterman approach. Not needed for all assets.
forecast_views = {
}
forecast_confidences = [
]


def get_data(date_from, date_to, assets, mar=None):
    """
        Get data for the selected list of assets
    """
    data_dict = {}

    asset = apps.get_model('portfolio', 'Asset')
    for ticker in assets:
        # Read from Database
        df = pd.read_csv(StringIO(asset.objects.get(name=ticker).historical_prices))
        
        df = df[(pd.to_datetime(df['timestamp']) >= date_from) 
            & (pd.to_datetime(df['timestamp']) <= date_to)]

        # Convert string to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        data_dict[ticker] = {}
        # Reverse dataframe, so we go from old to new date
        df = df.iloc[::-1]

        # Set timestamp as index, but also keep it as column
        df = df.set_index('timestamp', drop=False)

        df['daily_percent_change'] = pd.Series(df['adjusted_close'].pct_change(), index=df.index)

        data_dict[ticker]['df'] = df

        # Get metrics and add them to dict
        if ticker != "CASH":
            if ticker in crypto:
                metrics = calculate_metrics(df['daily_percent_change'], is_crypto=True, mar=mar)
            else:
                metrics = calculate_metrics(df['daily_percent_change'], is_crypto=False, mar=mar)

            data_dict[ticker]['max_drawdown'] = metrics['max_drawdown']
            data_dict[ticker]['sharpe'] = metrics['sharpe']
            data_dict[ticker]['sortino'] = metrics['sortino']
            data_dict[ticker]['calmar'] = metrics['calmar']
            data_dict[ticker]['daily_var_95'] = metrics['daily_var_95']
            data_dict[ticker]['cagr'] = metrics['cagr']
            data_dict[ticker]['volatility'] = metrics['volatility']
            data_dict[ticker]['downside_risk'] = metrics['downside_risk']
        else:
            data_dict[ticker]['max_drawdown'] = 0
            data_dict[ticker]['sharpe'] = 0
            data_dict[ticker]['sortino'] = 0
            data_dict[ticker]['calmar'] = 0
            data_dict[ticker]['daily_var_95'] = 0
            data_dict[ticker]['cagr'] = 0
            data_dict[ticker]['volatility'] = 0
            data_dict[ticker]['downside_risk'] = 0

    return data_dict

def get_asset_prices(assets_data):
        """
            Create a dataframe that consists of adjusted close prices of the selected instruments.
            Indexed with timestamp.

            The selected instruments are joined together using OUTER JOIN.
            For example, joining SPY with BTC will result with NaN values for SPY on weekends and holidays.

            Such NaN rows are then dropped before returning the dataframe.
        """
        extracted_data = []
        headers = []
        for ticker in list(assets_data.keys()):
            extracted_data.append(pd.DataFrame({
                ticker : assets_data[ticker]['df']['adjusted_close'].values
                },index=pd.DatetimeIndex(assets_data[ticker]['df']['timestamp'])))
            headers.append(ticker)
        
        # Balances timespans, so we only go from the date we have all assets onwards
        extracted_data_balanced = balance_timespans(extracted_data)
        df = pd.concat(extracted_data_balanced, axis=1)

        # Drops rows, where there are NaN values - e.g. weekends (TODO: this makes crypto not as accurate)
        df = df.dropna()

        return df

def get_asset_returns(assets_data):
        """
            Create a dataframe that consists of daily_percent_change of the selected instruments.
            Indexed with timestamp.

            The selected instruments are joined together using OUTER JOIN.
            For example, joining SPY with BTC will result with NaN values for SPY on weekends and holidays.
            Also joining data with more historical value with less historical will result in NaN values for the more historical values.

            Such NaN rows are then dropped before returning the dataframe.
        """
        extracted_data = []
        headers = []
        for ticker in list(assets_data.keys()):
            extracted_data.append(pd.DataFrame({
                ticker : assets_data[ticker]['df']['daily_percent_change'].values
                },index=pd.DatetimeIndex(assets_data[ticker]['df']['timestamp'])))
            headers.append(ticker)
        
        # Balances timespans, so we only go from the date we have all assets onwards
        extracted_data_balanced = balance_timespans(extracted_data)
        df = pd.concat(extracted_data_balanced, axis=1)

        # Drops rows, where there are NaN values - e.g. weekends (TODO: this makes crypto not as accurate)
        df = df.dropna()

        return df

def calculate_metrics(daily_returns, is_crypto = False, mar = None):
    
    """
        :param daily_returns: pandas Series daily returns
    """
    metrics = {}
    
    daily_returns = daily_returns[2:]

    if is_crypto:
        annualization = 365
    else:
        annualization = 252

    # Add a leading minus, to get a positive number - then we look for minimum DD
    metrics['max_drawdown'] = float(emp.max_drawdown(daily_returns))

    # We are taking default risk_free value of 0
    metrics['sharpe'] = emp.sharpe_ratio(daily_returns, annualization=annualization)
    metrics['calmar'] = emp.calmar_ratio(daily_returns, annualization=annualization)


    # Add a leading minus, to get a positive number - we will want minimum VaR
    metrics['daily_var_95'] = - emp.value_at_risk(daily_returns, 0.05)
    
    # Returns are the product of individual expected returns of asset and its weights 
    metrics['cagr'] = emp.annual_return(daily_returns, annualization=annualization)
    metrics['volatility'] = emp.annual_volatility(daily_returns, annualization=annualization)

    # Used for PMPT
    if mar == None:
        mar = metrics['cagr']

    # Downside risk using Semi-Deviation
    metrics['downside_risk'] = dside_risk(daily_returns, required_return=mar)
    metrics['sortino'] = emp.sortino_ratio(daily_returns, _downside_risk=metrics['downside_risk'], annualization=annualization)

    return metrics

def dside_risk(returns, required_return=0):
    """
    Empyrical library code, changed a bit.

    Determines the downside deviation below a threshold

    Parameters
    ----------
    returns : :py:class:`pandas.Series` or pd.DataFrame
        Daily returns of the strategy, noncumulative.
        See full explanation in :func:`~empyrical.stats.cum_returns`.
    required_return: :class:`float` / :py:class:`pandas.Series`
        minimum acceptable return

    Returns
    -------
    :class:`float`, or :py:class:`pandas.Series`

        Annualized downside deviation

    """
    if len(returns) < 1:
        return np.nan

    yearly_returns = emp.aggregate_returns(returns, 'yearly')
    
    downside_diff = _adjust_returns(yearly_returns, required_return)
    mask = downside_diff > 0
    downside_diff[mask] = 0.0
    squares = np.square(downside_diff)
    mean_squares = nanmean(squares, axis=0)
    dside_risk = np.sqrt(mean_squares)
    if len(yearly_returns.shape) == 2:
        dside_risk = pd.Series(dside_risk, index=yearly_returns.columns)

    return dside_risk

def _adjust_returns(returns, adjustment_factor):
    """
    Empyrical library code, internal class

    Returns a new :py:class:`pandas.Series` adjusted by adjustment_factor.
    Optimizes for the case of adjustment_factor being 0.

    Parameters
    ----------
    returns : :py:class:`pandas.Series`
    adjustment_factor : :py:class:`pandas.Series` / :class:`float`

    Returns
    -------
    :py:class:`pandas.Series`
    """
    if isinstance(adjustment_factor, (float, int)) and adjustment_factor == 0:
        return returns.copy()

    return returns - adjustment_factor

def balance_timespans(dataframes):
    """
        Argument is an array of dataframes.
        Each element contains date-value for a ticker.

        Return intersection of timestamps
    """
    min_date = get_min_date(dataframes)

    result = []
    for df in dataframes:
        df = df.loc[df.index > min_date]
        result.append(df)

    return result

def get_min_date(dataframes):
    """
        Argument is an array of dataframes.
        Each element contains date-value for a ticker.

        Return most recent starting timestamp.
    """

    min_date = pd.to_datetime(0, unit='s')

    for df in dataframes:
        if df.index[0] > min_date:
            min_date = df.index[0]
    
    return min_date


def benchmarks_returns(date_from, date_to):
    """
        Get cumulative returns for some benchmark portfolios
    """
    # Golden Buttefly 
    # 20% Total Stock Market ---- VTI
    # 20% Small Cap Value ----- IJS
    # 20% Long Term Bonds ----- TLT
    # 20% Short Term Bonds ---- SHY
    # 20% Gold ------ GLD
    butterfly_pf = {
        "VTI": 0.2,
        "IJS": 0.2,
        "TLT": 0.2,
        "SHY": 0.2,
        "GLD": 0.2,
    }

    # Dalio All Weather PF
    # 30%       Equity, U.S., Large Cap ---- SPY
    # 40%		TLT	iShares 20+ Year Treasury Bond	Bond, U.S., Long-Term
    # 15%		IEI	iShares 3-7 Year Treasury Bond	Bond, U.S., Intermediate-Term
    # 7.5%		GLD	SPDR Gold Trust	Commodity, Gold ------ GLD
    # 7.5%		GSG	iShares S&P GSCI Commodity Indexed Trust	Commodity, Broad Diversified ----- GSG
    dalio_pf = {
        "SPY": 0.3,
        "TLT": 0.4,
        "IEI": 0.15,
        "GLD": 0.075,
        "GSG": 0.075
    }

    benchmark_portfolios = {
        "Dalio All Weather": dalio_pf,
        "Golden Butterfly": butterfly_pf
    }

    assets = list(dalio_pf.keys())
    assets.extend(list(butterfly_pf.keys()))
    # Add SPY as benchmark portfolio
    assets.append("SPY")

    asset_data_dict = get_data(date_from, date_to, assets)
    assets_returns = get_asset_returns(asset_data_dict)

    benchmark_returns = {}
    for pf_name, pf_data in benchmark_portfolios.items():
        returns = 0
        for ticker, weight in pf_data.items():
            returns += assets_returns[ticker] * weight
        
        returns.rename(pf_name)
        benchmark_returns[pf_name] = returns     

    benchmark_returns["SPY"] = assets_returns["SPY"]   

    return benchmark_returns