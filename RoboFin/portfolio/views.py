from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from user.models import UserInfo
import json

def index(request):
    # Get current user's portfolio
    logged_user = request.user
    print(logged_user)
    try:
        logged_user_info = UserInfo.objects.get(user=logged_user)

        # Already completed questionare and has PF
        print()
        if logged_user_info.portfolio != None:
            metrics = json.loads(logged_user_info.portfolio.metrics)
            portfolio_weights = metrics['weights']
            portfolio_tickers = logged_user_info.portfolio.asset_tickers.split(',')

            portfolio_data = list(zip([pt.strip() for pt in portfolio_tickers], [pw * 100 for pw in portfolio_weights]))

            context = {
                'user': logged_user,
                'portfolio_data': portfolio_data
            }

            return render(request, 'portfolio/index.html', context)
        else:
            return render(request, 'portfolio/index.html')

    except Exception as e:
        return render(request, 'portfolio/index.html')
