from django.conf.urls import url
from apps.dev import views

urlpatterns = [
    url(r'^main/$', views.main),
    url(r'^doc/$', views.doc),
    url(r'^service/(\w+)/$', views.service),
]
