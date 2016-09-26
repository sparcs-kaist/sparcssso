from django.conf.urls import url
from apps.dev import views

urlpatterns = [
    url(r'^main/$', views.main),

    url(r'^service/(\w+)/$', views.service),
    url(r'^service/(\w+)/delete/$', views.service_delete),

    url(r'^user/(\w+)/$', views.user),
    url(r'^user/(\w+)/delete/$', views.user_delete),
]
