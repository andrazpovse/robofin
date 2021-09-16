from django.urls import path

from . import views

app_name = 'portfolio_performance'
urlpatterns = [
    path('', views.index, name='index'),
    path('crypto_crash/', views.crypto_crash, name='crypto_crash'),
    path('covid_drop/', views.covid_drop, name='covid_drop'),
    path('covid_recovery/', views.covid_recovery, name='covid_recovery')
]