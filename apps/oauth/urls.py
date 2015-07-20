from django.conf.urls import url

urlpatterns = [
    url(r'^require', 'apps.oauth.views.require'),
    url(r'^info', 'apps.oauth.views.info'),
]
