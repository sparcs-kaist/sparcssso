from django.conf.urls import url

urlpatterns = [
    # oauth section
    url(r'^require', 'apps.oauth.views.require'),
    url(r'^info', 'apps.oauth.views.info'),

    # profile section
    url(r'^service', 'apps.oauth.views.service'),

    # unregister section
    url(r'^unregister', 'apps.oauth.views.unregister'),
]
