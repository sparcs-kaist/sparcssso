from django.shortcuts import redirect
from django.urls import path

from apps.dev import views


urlpatterns = [
    path('', lambda x: redirect('/dev/main/')),
    path('main/', views.main),

    path('service/<str:name>/', views.service),
    path('service/<str:name>/delete/', views.service_delete),

    path('user/<str:uid>/', views.user),
    path('user/<str:uid>/delete/', views.user_delete),
]
