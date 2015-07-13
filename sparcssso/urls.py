"""sparcssso URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url, \
    handler400, handler403, handler404, handler500
from django.contrib import admin
from django.shortcuts import render

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^account/', include('apps.account.urls')),
]

handler400 = lambda request: render(request, 'error/400.html')
handler403 = lambda request: render(request, 'error/403.html')
handler404 = lambda request: render(request, 'error/404.html')
handler500 = lambda request: render(request, 'error/500.html')
