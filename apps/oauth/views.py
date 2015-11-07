from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.utils import timezone
from apps.oauth.models import Service, ServiceMap, AccessToken
import json
import os
import urllib


# make access token
def make_access_token(user, service):
    while True:
        tokenid = os.urandom(10).encode('hex')
        if len(AccessToken.objects.filter(tokenid=tokenid, service=service)) == 0:
            token = AccessToken(tokenid=tokenid, user=user, service=service)
            token.save()
            return token


# register service
def register_service(user, service):
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if m and not m.unregister_time:
        return 1, None
    elif m and m.unregister_time and \
            (timezone.now() - m.unregister_time).days < service.cooltime:
        return 2, None

    if m:
        m.delete()
    m = ServiceMap(user=user, service=service)

    while True:
        sid = os.urandom(10).encode('hex')
        if len(ServiceMap.objects.filter(sid=sid)) == 0:
            m.sid = sid
            m.register_time = timezone.now()
            m.unregister_time = None
            m.save()
            return 0, m


# unregister service
def unregister_service(user, service):
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if not m or m.unregister_time:
        return 1

    '''data = urllib.urlencoode({'sid': m.sid, 'key': service.secret_key})
    result = urllib.urlopen(service.unregister_url, data)
    result = json.load(result)

    status = result.get('status', '-1')
    if status != '0':
        return False
    '''

    m.unregister_time = timezone.now()
    m.save()
    return 0


# get call back url
def get_callback(user, service, url):
    is_test = user.profile.is_for_test
    if not is_test and not service:
        raise Http404()
    elif service:
        return service.callback_url
    return url


# /require/
@login_required
def require(request):
    name = request.GET.get('app', '')
    service = Service.objects.filter(name=name).first()

    url = request.GET.get('url', '')
    dest = get_callback(request.user, service, url)

    token = AccessToken.objects.filter(user=request.user, service=service).first()
    if token:
        token.delete()

    token = make_access_token(request.user, service)

    args = {'tokenid': token.tokenid}
    return redirect(dest + '?' + urllib.urlencode(args))


# /service/
@login_required
def service(request):
    user = request.user
    maps = ServiceMap.objects.filter(user=user, unregister_time=None)

    result_unreg = request.session.pop('result_unreg', -1)
    return render(request, 'oauth/service.html',
                  {'user': user, 'maps': maps, 'result_unreg': result_unreg})


# /unregister/
@login_required
def unregister(request):
    if request.method != 'POST':
        raise SuspiciousOperation()

    name = request.POST.get('app', '')
    service = Service.objects.filter(name=name).first()
    if not service:
        raise Http404()

    result = unregister_service(request.user, service)
    request.session['result_unreg'] = result
    return redirect('/oauth/service/')


def info(request):
    tokenid = request.GET.get('tokenid', '')
    token = AccessToken.objects.filter(tokenid=tokenid).first()
    if not token:
        raise Http404()

    user = token.user
    profile = user.profile
    service = token.service
    token.delete()

    code = 0
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if (not m or m.unregister_time) and service:
        code, m = register_service(user, service)

    sid = user.username
    if m and code != 2:
        sid = m.sid
    elif code == 2:
        sid = 'UNREGISTERED'

    resp = {}
    resp['uid'] = user.username
    resp['sid'] = sid
    resp['email'] = user.email
    resp['first_name'] = user.first_name
    resp['last_name'] = user.last_name
    resp['gender'] = profile.gender
    if profile.birthday:
        resp['birthday'] = profile.birthday.isoformat()
    else:
        resp['birthday'] = ''

    return HttpResponse(json.dumps(resp), content_type='application/json')

