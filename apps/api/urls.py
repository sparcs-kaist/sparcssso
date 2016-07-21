from django.conf.urls import url
from django.http import HttpResponse
from apps.api.views import v1, v2
import json


# /versions/
def versions(request):
    resp = {'versions': ['v1', 'v2']}
    return HttpResponse(json.dumps(resp), content_type='application/json')


urlpatterns = [
    url(r'^versions/$', versions),

    # VERSION 1 #
    url(r'^v1/logout/$', v1.logout),
    url(r'^v1/token/require/$', v1.token_require),
    url(r'^v1/token/info/$', v1.token_info),
    url(r'^v1/email/$', v1.email),
    url(r'^v1/notice/$', v1.notice),

    # Due to security problem (#84), point api was disabled until v2 release
    # url(r'^v1/point/$', v1.point),


    # VERSION 2 #
    url(r'^v2/token/require/$', v2.token_require),
    url(r'^v2/token/info/$', v2.token_info),
    url(r'^v2/logout/$', v2.logout),
    url(r'^v2/unregister/$', v2.unregister),
    url(r'^v2/point/$', v2.point),
    url(r'^v2/notice/$', v2.notice),
    url(r'^v2/email/$', v2.email),
    url(r'^v2/stats/$', v2.stats),
]
