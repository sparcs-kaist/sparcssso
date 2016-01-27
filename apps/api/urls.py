from django.conf.urls import url
from apps.api.views import v0, v1

urlpatterns = [
    url(r'^versions/$', v1.versions),

    # VERSION 0 #
    url(r'^token/require/$', v0.token_require),
    url(r'^token/info/$', v0.token_info),
    url(r'^point/$', v0.point),
    url(r'^email/$', v0.email),

    # VERSION 1 #
    url(r'^v1/token/require/$', v1.token_require),
    url(r'^v1/token/info/$', v1.token_info),
    url(r'^v1/point/$', v1.point),
    url(r'^v1/email/$', v1.email),
    url(r'^v1/notice/$', v1.notice),
]
