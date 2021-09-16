from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from user.models import UserInfo
import json
from cronjobs.jobs.common import get_data, events, get_asset_returns, forecast_confidences, forecast_views, calculate_metrics
import cronjobs.jobs.common as common
import pandas as pd

def index(request, date_from=pd.to_datetime("2017-10-01"), date_to=pd.to_datetime("2021-08-01")):
    # Get current user's portfolio
    logged_user = request.user
    print(logged_user)
    try:
        logged_user_info = UserInfo.objects.get(user=logged_user)

        # Already completed questionare and has PF
        if logged_user_info.portfolio != None:
            if logged_user_info.starting_capital != None:
                starting_capital = int(logged_user_info.starting_capital)
            else:
                starting_capital = 10*1000
            
            metrics = json.loads(logged_user_info.portfolio.metrics)
            portfolio_weights = metrics['weights']
            portfolio_tickers = [ticker.strip() for ticker in logged_user_info.portfolio.asset_tickers.split(',')]

            non_zero_weights = []
            non_zero_tickers = []
            for idx in range(0, len(portfolio_weights)):
                if portfolio_weights[idx] != 0:
                    non_zero_weights.append(portfolio_weights[idx])
                    non_zero_tickers.append(portfolio_tickers[idx])

            historical_data = get_data(date_from, date_to, non_zero_tickers)
            # Historical returns for each ticker
            historical_returns = get_asset_returns(historical_data)

            # Multiplied by initial investment
            historical_returns = (historical_returns + 1).cumprod()*starting_capital
            dates = [pd.to_datetime(x).strftime('%Y-%m-%d') for x in list(historical_returns.index.values)]


            # Historical returns and values for our portfolio
            historical_returns_weight_adjusted = historical_returns*non_zero_weights
            portfolio_returns = (historical_returns_weight_adjusted).sum(axis=1)

            # Plot with starting capital as initial investment
            cumulative_returns = {}
            cumulative_returns["Your Portfolio"] = list(zip(dates, (portfolio_returns).values.tolist()))

            # Add equal weight portfolio
            equal_weight_pf_weights = []

            # Count cryptocurrencies
            crypto_count = 0
            for ticker in non_zero_tickers:
                if ticker in common.crypto:
                    crypto_count += 1

            for ticker in non_zero_tickers:
                if ticker in common.crypto:
                    equal_weight_pf_weights.append(1 / (len(non_zero_tickers) + (1 if crypto_count > 0 else 0)) / crypto_count)
                else:
                    equal_weight_pf_weights.append(1 / (len(non_zero_tickers) + (1 if crypto_count > 0 else 0) - crypto_count))

            historical_returns_weight_adjusted = historical_returns*equal_weight_pf_weights
            portfolio_returns = (historical_returns_weight_adjusted).sum(axis=1)

            cumulative_returns["Equal Weights"] = list(zip(dates, (portfolio_returns).values.tolist()))

            # Add benchmark portfolios to cumulative returns
            benchmark_portfolios = common.benchmarks_returns(date_from, date_to)

            for name, value in benchmark_portfolios.items():
                cumulative_returns[name] = list(zip(dates, ((value + 1).cumprod()*starting_capital).tolist()))

            context = {
                'user': logged_user,
                'cumulative_returns': cumulative_returns
            }

            return render(request, 'portfolio_performance/index.html', context)
        else:
            return render(request, 'portfolio_performance/index.html')

    except Exception as e:
        return render(request, 'portfolio_performance/index.html')

def crypto_crash(request):
    return index(request, date_from=pd.to_datetime("2017-12-10"), date_to=pd.to_datetime("2019-03-03"))

def covid_drop(request):
    return index(request, date_from=pd.to_datetime("2020-02-06"), date_to=pd.to_datetime("2020-08-24"))

def covid_recovery(request):
    return index(request, date_from=pd.to_datetime("2020-08-24"), date_to=pd.to_datetime("2021-08-01"))
