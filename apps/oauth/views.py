from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import HttpResponse, Http404
from apps.oauth.models import AccessToken, Service
import json
import os
import urllib


# Helper functions
def generate_token(user):
    while True:
        uid = os.urandom(10).encode('hex')
        if len(AccessToken.objects.filter(uid=uid)) == 0:
            token = AccessToken(uid=uid, user=user)
            token.save()
            return uid


def get_callback(user, app_name, url):
    is_test = user.user_profile.is_for_test
    app = Service.objects.filter(name=app_name)
    if not is_test and not app:
        raise Http404()
    elif app:
        return app[0].callback_url
    return url


@login_required
def require(request):
    app_name = request.GET.get('app', '')
    url = request.GET.get('url', '')
    dest = get_callback(request.user, app_name, url)

    token = AccessToken.objects.filter(user=request.user)
    if len(token) > 0:
        uid = token[0].uid
    else:
        uid = generate_token(request.user)

    args = {'uid': uid}
    return redirect(dest + '?' + urllib.urlencode(args))


def info(request):
    uid = request.GET.get('uid', '')
    token = AccessToken.objects.filter(uid=uid).first()
    if token is None:
        raise Http404()

    user = token.user
    profile = user.user_profile
    token.delete()

    resp = {}
    resp['username'] = user.username
    resp['email'] = user.email
    resp['first_name'] = user.first_name
    resp['last_name'] = user.last_name
    resp['gender'] = profile.gender
    if profile.birthday:
        resp['birthday'] = profile.birthday.isoformat()
    else:
        resp['birthday'] = ''

    return HttpResponse(json.dumps(resp), content_type='application/json')
