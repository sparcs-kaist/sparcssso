import json
import time

from django.conf.urls import url
from django.http import HttpResponse

from .views import v2


# /versions/
def versions(request):
    resp = {
        'versions': ['v2', ],
        'timestamp': int(time.time()),
    }
    return HttpResponse(json.dumps(resp), content_type='application/json')


urlpatterns = [
    url(r'^versions/$', versions),

    # VERSION 2 #
    url(r'^v2/token/require/$', v2.token_require),
    url(r'^v2/token/info/$', v2.token_info),
    url(r'^v2/logout/$', v2.logout),
    url(r'^v2/point/$', v2.point),
    url(r'^v2/notice/$', v2.notice),
    url(r'^v2/email/$', v2.email),
    url(r'^v2/stats/$', v2.stats),
]
