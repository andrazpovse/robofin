# Create optimal portfolio
from .risk import Risk, RiskTollerance
from .common import get_data, events, get_asset_prices, forecast_confidences, forecast_views, calculate_metrics
import numpy as np
import math
import pandas as pd
import empyrical as emp
import sys
import random
from pypfopt import black_litterman, risk_models
from pypfopt import BlackLittermanModel, plotting

DECIMAL_PLACES = 3
SINGLE_WEIGHT_THRESHOLD = 0.01

class OptimalPortfolioGenerator:
    """
        OptimalPortfolioGenerator class takes care of generating an optimal portfolio based on input.

    """
    def __init__(self, risk, etf, crypto, iterations = 1000, date_from=None, date_to=None, event=None,
        use_black_litterman=False, use_pmpt_approach=False):
        if event is None and (date_from is None or date_to is None):
            raise Exception('Dates or event must be specified.') 

        self.risk = risk
        self.etf = etf
        self.crypto = crypto
        self.iterations = iterations

        self.assets = etf.copy()
        self.assets.extend(crypto)

        if event is not None:
            # Get dates from the event
            date_from = events[event].date_from
            date_to = events[event].date_to

        self.use_black_litterman = use_black_litterman
        self.asset_data_dict = get_data(date_from, date_to, self.assets)
        self.assets_prices = get_asset_prices(self.asset_data_dict)
        self.weight_limits = self.get_weight_limits(use_pmpt_approach)

    def get_optimal_portfolio(self, portfolios):
        """
            Returns dictionary of optimal portfolios with names as keys.
        """
        optimal_portfolios = {}

        # Max Sharpe        
        # optimal_portfolios['max_sharpe_portfolio'] = portfolios.iloc[(portfolios['sharpe']).idxmax()]

        distinct_returns_portfolios = portfolios.round(
                {'cagr': DECIMAL_PLACES, 'volatility': DECIMAL_PLACES}).sort_values(
            ['cagr', 'volatility', 'max_drawdown'], ascending=False).drop_duplicates(
            subset='cagr', keep="last")

        drp_copy = distinct_returns_portfolios.copy()
        for i, row in drp_copy.iterrows():
            if row['max_drawdown'] <= self.risk.max_drawdown or \
               row['cagr'] <= self.risk.cagr_target or \
               row['volatility'] > self.risk.max_volatility:
                distinct_returns_portfolios = distinct_returns_portfolios.drop(i, errors='ignore')

        distinct_returns_portfolios.sort_values(by=['sharpe'], inplace=True, ascending=True)
        optimal_portfolios['choosen_portfolio_MPT'] = distinct_returns_portfolios.iloc[distinct_returns_portfolios.shape[0]-1].squeeze()

        return optimal_portfolios


    def generate_portfolios(self):
        percent_changes = self.assets_prices.pct_change()
        assets_cagrs = emp.annual_return(percent_changes)

        # Alter CAGRS with Black-Litterman approach using our views
        if self.use_black_litterman:
            S = risk_models.CovarianceShrinkage(self.assets_prices).ledoit_wolf()
            bl = BlackLittermanModel(S, pi=assets_cagrs, absolute_views=forecast_views,
                 omega="idzorek", view_confidences=forecast_confidences)


        data = {'weights': [], 'max_drawdown': [], 'sharpe': [],
            'sortino': [], 'calmar': [], 'daily_var_95': [], 'cagr': [],
            'volatility': [], 'downside_risk': []}

        iterations = self.iterations
        while (iterations > 0):
            weights = []
            
            for limit in self.weight_limits:
                weights.append(random.randint(0, limit*math.pow(10, DECIMAL_PLACES)) / math.pow(10, DECIMAL_PLACES))

            # If a weight is less than threshold, set it to 0.
            weights = [0 if w < SINGLE_WEIGHT_THRESHOLD else w for w in weights]

            # Sum of all is 1
            weights = weights/np.sum(weights)

            # Round weights
            weights = [round(w, DECIMAL_PLACES) for w in weights]
                        
            if (sum(weights) != 1):
                continue

            if all([generated <= limit for generated, limit in zip(weights, self.weight_limits)]):
                portfolio_returns = pd.Series((percent_changes.multiply(weights, axis=1)).sum(axis=1))
                data['weights'].append(weights)
                for key,value in calculate_metrics(portfolio_returns, self.risk.cagr_target).items():
                    data[key].append(value)
                iterations -= 1
            
        # "Always" include portfolios with 100% of a single instrument
        # When there is a max weight limit for such instrument, do not include it.
        for i in range(len(self.assets)):
            weights = np.zeros(len(self.assets))
            weights[i] = 1
            if all([generated <= limit for generated, limit in zip(weights, self.weight_limits)]):
                portfolio_returns = pd.Series((percent_changes.multiply(weights, axis=1)).sum(axis=1))
                data['weights'].append(weights)
                for key,value in calculate_metrics(portfolio_returns, self.risk.cagr_target).items():
                    data[key].append(value)

        print("Finished calculating portfolios")

        return pd.DataFrame(data)

    def get_weight_limits(self, use_pmpt_approach):
        """
            Define max weight limit for asset in portfolio based on Risk
            and the metrics of the asset
        """
        weight_limits = []
        crypto_weight = 0

        for ticker in self.assets:
            yr_volatility = self.asset_data_dict[ticker]['volatility']        

            # Leading minus to get positive number
            max_drawdown = -self.asset_data_dict[ticker]['max_drawdown']

            # use them as input to the formula
            if self.risk.risk_tollerance == RiskTollerance.VeryLow:
                x = 0.25
            elif self.risk.risk_tollerance == RiskTollerance.Low:
                x = 1
            elif self.risk.risk_tollerance == RiskTollerance.Medium:
                x = 3
            elif self.risk.risk_tollerance == RiskTollerance.High:
                x = 4
            elif self.risk.risk_tollerance == RiskTollerance.VeryHigh:
                x = 5
            
            if ticker == "CASH":
                weight_limits.append(self.risk.max_cash)
            elif self.risk.risk_tollerance == RiskTollerance.Extreme:
                # Create no upper weight limit for extreme portfolio
                weight_limits.append(1)
            elif ticker in self.crypto:
                if use_pmpt_approach:
                    weight_limits.append(x/(self.asset_data_dict[ticker]['downside_risk']*2))
                else:
                    weight_limits.append(x/yr_volatility)

                crypto_weight += weight_limits[-1]
            else:
                # Rounded to 3 decimal places (0.1% precision)
                if use_pmpt_approach:
                    """
                        If using PMPT approach, we multiply downside risk by 2, 
                        which penalizes tickers with more downside than upside risk.
                        This way, tickers with more downside risk, will get lower weight limit whereas 
                        tickers with less downside risk (than upside) will get a higher weight limit.
                    """
                    downside_risk = self.asset_data_dict[ticker]['downside_risk']
                    weight_limits.append(round(np.clip(x/(math.pow(downside_risk*2 , 2) * 100), 0, 1), DECIMAL_PLACES))
                else:
                    weight_limits.append(round(np.clip(x/(math.pow(yr_volatility , 2) * 100), 0, 1), DECIMAL_PLACES))

            if ticker in self.crypto:
                crypto_weight += weight_limits[-1]

        # Upper weight for entire cryptocurrency asset class is set with risk profile
        if crypto_weight > self.risk.max_crypto and self.risk.risk_tollerance != RiskTollerance.Extreme:
            for idx in range(1, len(self.crypto) + 1):
                weight_limits[-idx] = np.round(weight_limits[-idx]/crypto_weight*self.risk.max_crypto, DECIMAL_PLACES)


        return weight_limits
        


