from django.conf.urls import url
from apps.api.views import v1

urlpatterns = [
    url(r'^versions/$', v1.versions),

    # VERSION 1 #
    url(r'^v1/logout/$', v1.logout),
    url(r'^v1/token/require/$', v1.token_require),
    url(r'^v1/token/info/$', v1.token_info),

    # Due to security problem (#84), point api was disabled until v2 release
    # url(r'^v1/point/$', v1.point),

    url(r'^v1/email/$', v1.email),
    url(r'^v1/notice/$', v1.notice),
]
