from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.core.validators import URLValidator
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from apps.core.backends import reg_service, validate_email
from apps.core.models import Service, ServiceMap, AccessToken, PointLog
import json
import logging
import os
import urllib


logger = logging.getLogger('sso.api')
profile_logger = logging.getLogger('sso.core.profile')


# get call back url
def get_callback(user, service, url):
    is_test = user.profile.is_for_test
    if not is_test and not service:
        raise Http404()
    elif service:
        return service.callback_url

    validate = URLValidator()
    try:
        validate(url)
    except:
        raise Http404()
    return url


# /require/
@login_required
def token_require(request):
    name = request.GET.get('app', '')
    service = Service.objects.filter(name=name).first()

    url = request.GET.get('url', '')
    dest = get_callback(request.user, service, url)

    if name.startswith('sparcs') and not request.user.profile.sparcs_id:
        return HttpResponseForbidden()

    token = AccessToken.objects.filter(user=request.user, service=service).first()
    if token:
        logger.info('token.delete', {'r': request, 'hide': True})
        token.delete()

    m = ServiceMap.objects.filter(user=request.user, service=service).first()

    if (not m or m.unregister_time) and service:
        result = reg_service(request.user, service)
        if result:
            profile_logger.info('register.success: app=%s' % service.name, {'r': request})
        else:
            d = service.cooltime - (timezone.now() - m.unregister_time).days
            profile_logger.warning('register.fail: app=%s' % service.name, {'r': request})
            return render(request, 'api/cooltime.html', {'service': service, 'left': d})

    while True:
        tokenid = os.urandom(10).encode('hex')
        if not AccessToken.objects.filter(tokenid=tokenid, service=service).count():
            break

    token = AccessToken(tokenid=tokenid, user=request.user, service=service)
    token.save()
    logger.info('token.create: app=%s,url=%s' % (name, url), {'r': request})
    args = {'tokenid': token.tokenid}
    return redirect(dest + '?' + urllib.urlencode(args))


# /info/
def token_info(request):
    tokenid = request.GET.get('tokenid', '')
    token = AccessToken.objects.filter(tokenid=tokenid).first()
    if not token:
        raise Http404()

    user = token.user
    profile = user.profile
    service = token.service
    logger.info('token.delete', {'r': request, 'hide': True})
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
    if profile.kaist_info_time:
        resp['kaist_info_time'] = profile.kaist_info_time.isoformat()
    else:
        resp['kaist_info_time'] = ''
    resp['sparcs_id'] = profile.sparcs_id

    return HttpResponse(json.dumps(resp), content_type='application/json')


# /point/
@csrf_exempt
def point(request):
    if request.method != 'POST':
        raise SuspiciousOperation()

    name = request.POST.get('app', '')
    service = Service.objects.filter(name=name).first()
    if not service:
        raise Http404()

    key = request.POST.get('key', '')
    if service.secret_key != key:
        raise SuspiciousOperation()

    sid = request.POST.get('sid', '')
    m = ServiceMap.objects.filter(sid=sid, service=service).first()
    if not m:
        raise Http404()

    delta = int(request.POST.get('delta', '0'))
    action = request.POST.get('action', '')
    lock = request.POST.get('lock', '')
    lower_bound = int(request.POST.get('lower_bound', '-100000000'))

    profile = m.user.profile
    point = profile.point
    changed = False
    if delta and (lock == '' or point >= lower_bound):
        point += delta
        manager = m.user.point_logs
        if manager.count() >= 20:
            manager.order_by('time')[0].delete()
        PointLog(user=m.user, service=service, delta=delta, point=point,
                 action=action).save()

        logger.info('point: app=%s,delta=%d' % (service.name, delta),
                    {'r': request, 'uid': m.user.username, 'hide': True})
        profile.point = point
        profile.save()
        changed = True

    return HttpResponse(json.dumps({'point': point, 'changed': changed}),
                        content_type='application/json')


# /email/
def email(request):
    if validate_email(request.GET.get('email', '')):
        return HttpResponse(status=200)
    return HttpResponse(status=400)
