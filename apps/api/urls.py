import json
import time

from django.conf import settings
from django.http import HttpResponse
from django.urls import path

from apps.api.views import v2
from apps.core.views import auth


# /versions/
def versions(request):
    resp = {
        'versions': ['v2'],
        'timestamp': int(time.time()),
    }
    return HttpResponse(json.dumps(resp), content_type='application/json')


urlpatterns = [
    path('versions/', versions),

    # VERSION 2 #
    path('v2/token/require/', v2.TokenRequireView.as_view()),
    path('v2/token/info/', v2.TokenInfoView.as_view()),
    path('v2/logout/', v2.logout),
    path('v2/point/', v2.point),
    path('v2/notice/', v2.NoticeView.as_view()),
    path('v2/email/', v2.EmailView.as_view()),
    path('v2/stats/', v2.stats),
]

if settings.KAIST_APP_V2_ENABLED:
    urlpatterns += [
        path('idp/kaist/callback', auth.callback_kaist_v2)
    ]
