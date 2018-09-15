import json
import time

from django.http import HttpResponse
from django.urls import path

from apps.api.views import v2


# /versions/
def versions(request):
    resp = {
        'versions': ['v2', ],
        'timestamp': int(time.time()),
    }
    return HttpResponse(json.dumps(resp), content_type='application/json')


urlpatterns = [
    path('versions/', versions),

    # VERSION 2 #
    path('v2/token/require/', v2.token_require),
    path('v2/token/info/', v2.token_info),
    path('v2/logout/', v2.logout),
    path('v2/point/', v2.point),
    path('v2/notice/', v2.notice),
    path('v2/email/', v2.email),
    path('v2/stats/', v2.stats),
]
