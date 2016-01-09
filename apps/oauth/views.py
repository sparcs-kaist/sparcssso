from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.utils import timezone
from apps.oauth.models import Service, ServiceMap, AccessToken
import json
import logging
import os
import urllib


logger = logging.getLogger('sso.oauth')


# make access token
def make_access_token(user, service):
    while True:
        tokenid = os.urandom(10).encode('hex')
        if len(AccessToken.objects.filter(tokenid=tokenid, service=service)) == 0:
            token = AccessToken(tokenid=tokenid, user=user, service=service)
            token.save()
            return token


# register service
def register_service(request, user, service):
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if m and not m.unregister_time:
        logger.warning('service.register.fail: already registered, name=%s' % service.name, request)
        return False
    elif m and m.unregister_time and \
            (timezone.now() - m.unregister_time).days < service.cooltime:
        logger.warning('service.register.fail: in cooltime, name=%s' % service.name, request)
        return False

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

            logger.info('service.register.success: name=%s' % service.name, request)
            return True


# unregister service
def unregister_service(request, user, service):
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if not m or m.unregister_time:
        logger.warning('service.unregister.fail: target not exists, name=%s' % service.name, request)
        return 1

    data = urllib.urlencoode({'sid': m.sid, 'key': service.secret_key})
    result = urllib.urlopen(service.unregister_url, data)

    """try:
        result = json.load(result)

        status = result.get('status', '-1')
        if status != '0':
            return False
    except:
        return False"""

    m.unregister_time = timezone.now()
    m.save()

    logger.info('service.unregister.success: name=%s' % service.name, request)
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
        logger.info('accesstoken.revoke', request)
        token.delete()

    m = ServiceMap.objects.filter(user=request.user, service=service).first()

    fail = False
    if (not m or m.unregister_time) and service:
        fail = not register_service(request, request.user, service)

    if fail:
        d = service.cooltime - (timezone.now() - m.unregister_time).days
        return render(request, 'oauth/cooltime.html', {'service': service, 'left': d})

    token = make_access_token(request.user, service)
    logger.info('accesstoken.make: app=%s, url=%s' % (name, url), request)
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

    result = unregister_service(request, request.user, service)
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

    m = ServiceMap.objects.filter(user=user, service=service).first()
    sid = user.username
    if m:
        sid = m.sid

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
    resp['is_for_test'] = profile.is_for_test
    resp['facebook_id'] = profile.facebook_id
    resp['twitter_id'] = profile.twitter_id
    resp['kaist_id'] = profile.kaist_id
    resp['kaist_info'] = profile.kaist_info
    resp['sparcs_id'] = profile.sparcs_id

    return HttpResponse(json.dumps(resp), content_type='application/json')

