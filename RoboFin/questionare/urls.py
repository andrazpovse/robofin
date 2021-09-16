from django.urls import path

from . import views

app_name = 'questionare'
urlpatterns = [
    path('', views.index, name='index'),
    path('submit_questionare/', views.submit_questionare, name='submit_questionare'),
    path('redo_questionare/', views.redo_questionare, name='redo_questionare')
]