from django.urls import path

from . import views

app_name = 'user'
urlpatterns = [
    path('', views.index, name='index'),
    path('user_login/', views.user_login, name='user_login'),
    path('register/', views.register, name='register')
]