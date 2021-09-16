from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from .models import Question
from django.urls import reverse
from user.models import UserInfo
from portfolio.models import Portfolio

def index(request):
    questions = Question.objects.all()
    logged_user = request.user
    try:
        logged_user_info = UserInfo.objects.get(user=logged_user)

        # Already completed questionare
        if logged_user_info.risk_score != None:
            context = {
                'risk_score': logged_user_info.risk_score
            }
            return render(request, 'questionare/index.html', context)

    except Exception as e:
        print(e)

    context = {
        'questions': questions,
    }
    return render(request, 'questionare/index.html', context)

def redo_questionare(request):
    logged_user = request.user
    try:
        # Remove risk_score from user
        logged_user_info = UserInfo.objects.get(user=logged_user)
        logged_user_info.risk_score = None
        logged_user_info.save()
    except Exception as e:
        print(e)
        
    return HttpResponseRedirect(reverse('questionare:index'))

def submit_questionare(request):
    risk_score = 0

    for key, value in request.POST.items():
        if key != 'csrfmiddlewaretoken':
            risk_score += int(value)

    logged_user = request.user
    if logged_user.is_authenticated:
        # Assign score to user (and give him a portfolio)
        try:
            # Add Risk Score to user. TODO: Give him a portfolio
            logged_user_info = UserInfo.objects.get(user=logged_user)
            logged_user_info.risk_score = risk_score
            logged_user_info.portfolio = Portfolio.objects.get(risk_score=risk_score)
            logged_user_info.save()
        except Exception as e:
            return HttpResponseRedirect(reverse('questionare:index'))

        return HttpResponseRedirect(reverse('questionare:index'))
    else:
        return HttpResponse("Please login")

