from django.conf.urls import url
from django.shortcuts import redirect

from . import views


urlpatterns = [
    url(r'^$', lambda x: redirect('/dev/main/')),
    url(r'^main/$', views.main),

    url(r'^service/(\w+)/$', views.service),
    url(r'^service/(\w+)/delete/$', views.service_delete),

    url(r'^user/(\w+)/$', views.user),
    url(r'^user/(\w+)/delete/$', views.user_delete),
]
