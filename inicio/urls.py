from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('homePage/', views.homePage, name='homePage'),
]