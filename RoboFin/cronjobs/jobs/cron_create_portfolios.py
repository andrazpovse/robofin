import sys
from .risk import Risk
from .optimal_portfolio_generator import OptimalPortfolioGenerator
from copy import deepcopy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
from django.apps import apps

def insert_into_db(portfolio, date_from, date_to, risk_score, asset_tickers):
    portfolio_model = apps.get_model('portfolio', 'Portfolio')
    portfolio_asset_model = apps.get_model('portfolio', 'PortfolioAsset')
    asset = apps.get_model('portfolio', 'Asset')

    # Create if not exists, else update with new data
    pf, created = portfolio_model.objects.update_or_create(
        risk_score = risk_score,
        defaults = {
            'asset_tickers': ", ".join(asset_tickers),
            'metrics': portfolio.to_json(),
            'name': "Portfolio for Risk score: {rf}".format(rf=risk_score),
            'start_date': date_from,
            'end_date': date_to
        }
    )

    for idx, ticker in enumerate(asset_tickers):
        portfolio_asset_model.objects.update_or_create(
            portfolio = pf,
            asset = asset.objects.get(name=ticker),
            defaults = {
                'allocation': portfolio['weights'][idx]
            }
        )


def run():
    np.seterr(divide='ignore', invalid='ignore')
    iterations = 10000
    
    # CRON JOB
    # Builds portfolios for all possible risk profiles
    train_date_from = pd.to_datetime("2017-10-01")
    train_date_to = pd.to_datetime("2021-08-01")

    etf = ['AGG', 'SHY', 'SPY', 'QQQ', 'EWG', 'XLU', 'GSG', 'GLD']
    crypto = ['ETH', 'BTC', 'BNB', 'ADA', 'XRP']

    etf.append('CASH')
    
    # Calculate portfolios for each risk score
    for risk_score in range(6,64):
        start_time = time.perf_counter()
        risk = Risk(risk_score)
        
        # 2 calculate optimal portfolio on some timespan -- assume ideal PF weights
        optimalPortfolioGenerator = OptimalPortfolioGenerator(risk, etf, crypto, iterations=iterations, 
            date_from=train_date_from, date_to=train_date_to,
            use_black_litterman=False, use_pmpt_approach=False)

        portfolios = optimalPortfolioGenerator.generate_portfolios()
        optimal_portfolios = optimalPortfolioGenerator.get_optimal_portfolio(portfolios)

        # Pick optimal MPT portfolio
        optimal_portfolio = optimal_portfolios["choosen_portfolio_MPT"]
        insert_into_db(optimal_portfolio, train_date_from, train_date_to, risk_score, optimalPortfolioGenerator.assets)
        end_time = time.perf_counter()
        print("Created portfolio for risk score {rs} in : {et} seconds.".format(rs=str(risk_score), et=end_time-start_time))

    
if __name__ == "__main__":
    run()

