from django.conf.urls import url

urlpatterns = [
    url(r'^require', 'apps.oauth.views.require'),
    url(r'^info', 'apps.oauth.views.info'),

    url(r'^profile', 'apps.oauth.views.profile'),
    url(r'^unregister', 'apps.oauth.views.unregister'),
]
