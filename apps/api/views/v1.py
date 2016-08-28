from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.validators import URLValidator
from django.contrib import auth
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from apps.core.backends import reg_service, validate_email
from apps.core.models import Notice, Service, ServiceMap, AccessToken, PointLog
from datetime import timedelta
import datetime
import hmac
import json
import logging
import os
import urllib


logger = logging.getLogger('sso.api')
profile_logger = logging.getLogger('sso.core.profile')


def date2str(obj):
    if obj:
        return obj.isoformat()
    return ''


# get call back url
def get_callback(user, service, url):
    is_test = user.profile.test_enable
    if not is_test and not service:
        return None
    elif service:
        return service.login_callback_url

    validate = URLValidator()
    try:
        validate(url)
    except:
        raise Http404()
    return url


# /logout/
@login_required
def logout(request):
    name = request.GET.get('app', '')
    service = Service.objects.filter(name=name).first()
    if not service:
        return redirect('/')

    time = request.GET.get('time', '0')
    time = int(time) if time.isdigit() else 0

    date = datetime.datetime.fromtimestamp(time, timezone.utc)
    now = timezone.now()
    if abs((now - date).total_seconds()) > 10:
        return redirect(service.main_url)

    sm = ServiceMap.objects.filter(user=request.user, service=service).first()
    if not sm:
        return redirect(service.main_url)

    m = hmac.new(str(service.secret_key),
                 str('%s:%s' % (time, sm.sid))).hexdigest()
    m_client = request.GET.get('m', '')
    if constant_time_compare(m, m_client):
        logger.info('logout', {'r': request})
        auth.logout(request)

    return redirect(service.main_url)


# /token/require/
@login_required
def token_require(request):
    name = request.GET.get('app', '')
    service = Service.objects.filter(name=name).first()

    url = request.GET.get('url', '')
    dest = get_callback(request.user, service, url)

    alias = service.alias if service else url

    reason = 0
    if request.user.is_superuser:
        reason = 1
    elif name.startswith('sparcs') and not request.user.profile.sparcs_id:
        reason = 2
    elif not dest:
        reason = 3

    if reason:
        return render(request, 'api/denied.html',
                      {'reason': reason, 'alias': alias, 'dest': dest})

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

    token = AccessToken(tokenid=tokenid, user=request.user, service=service,
                        expire_time=timezone.now() + timedelta(seconds=5))
    token.save()
    logger.info('token.create: app=%s,url=%s' % (name, url), {'r': request})
    args = {'tokenid': token.tokenid}
    return redirect(dest + '?' + urllib.urlencode(args))


# /token/info/
@csrf_exempt
def token_info(request):
    if request.method != 'POST':
        raise PermissionDenied()

    tokenid = request.POST.get('tokenid', '')
    token = AccessToken.objects.filter(tokenid=tokenid).first()
    if not token:
        raise Http404()

    user = token.user
    profile = user.profile
    service = token.service
    logger.info('token.delete', {'r': request, 'hide': True})
    token.delete()

    if token.expire_time < timezone.now():
        raise Http404()

    key = request.POST.get('key', '')
    if token.service and token.service.secret_key != key:
        raise PermissionDenied()

    m = ServiceMap.objects.filter(user=user, service=service).first()
    sid = user.username
    if m:
        sid = m.sid

    resp = {
        'uid': user.username,
        'sid': sid,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'gender': profile.gender,
        'birthday': date2str(profile.birthday),
        'is_for_test': profile.test_enabled,
        'facebook_id': profile.facebook_id,
        'twitter_id': profile.twitter_id,
        'kaist_id': profile.kaist_id,
        'kaist_info': profile.kaist_info,
        'kaist_info_time': date2str(profile.kaist_info_time),
        'sparcs_id': profile.sparcs_id
    }

    return HttpResponse(json.dumps(resp), content_type='application/json')


# /point/
@csrf_exempt
@transaction.atomic
def point(request):
    if request.method != 'POST':
        raise PermissionDenied()

    name = request.POST.get('app', '')
    service = Service.objects.filter(name=name).first()
    if not service:
        raise Http404()

    key = request.POST.get('key', '')
    if service.secret_key != key:
        raise PermissionDenied()

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


# /notice/
def notice(request):
    current_time = timezone.now()
    notice = Notice.objects.filter(valid_from__lte=current_time,
                                   valid_to__gt=current_time).first()
    resp = {}
    if notice:
        resp = notice.to_dict()
    return HttpResponse(json.dumps(resp), content_type='application/json')
