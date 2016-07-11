from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.core.validators import URLValidator
from django.contrib import auth
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from apps.core.backends import reg_service, validate_email
from apps.core.models import Notice, Service, ServiceMap, AccessToken, PointLog
from datetime import timedelta
from datetime import datetime
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


def extract_flag(flags):
    result = []
    if flags['test']:
        result.append('TEST')
    if flags['sparcs']:
        result.append('SPARCS')
    return result


# /token/require/
@login_required
def token_require(request):
    client_id = request.GET.get('client_id', '')
    state = request.GET.get('state', '')

    if len(state) < 8:
        raise SuspiciousOperation()

    service = Service.objects.filter(name=client_id).first()
    if not service:
        raise SuspiciousOperation()

    user = request.user
    flags = user.flags

    reason = 0
    if flags['sysop']:
        reason = 1
    elif service.scope == 'SPARCS' and not flags['sparcs']:
        reason = 2
    elif service.scope == 'TEST' and not flags['test']:
        reason = 3

    if reason:
        return render(request, 'api/denied.html',
                      {'reason': reason, 'alias': service.alias})

    token = AccessToken.objects.filter(user=user, service=service).first()
    if token:
        logger.info('token.delete', {'r': request, 'hide': True})
        token.delete()

    m = ServiceMap.objects.filter(user=user, service=service).first()
    if not m or m.unregister_time:
        result = reg_service(user, service)
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

    token = AccessToken(tokenid=tokenid, user=user, service=service,
                        expire_time=timezone.now() + timedelta(seconds=5))
    token.save()
    logger.info('token.create: app=%s' % client_id, {'r': request})

    args = {'tokenid': token.tokenid}
    return redirect(service.login_callback_url + '?' + urllib.urlencode(args))


# /token/info/
@csrf_exempt
def token_info(request):
    if request.method != 'POST':
        raise SuspiciousOperation()

    client_id = request.POST.get('client_id', '')
    code = request.POST.get('code', '')
    timestamp = request.POST.get('timestamp', '0')
    timestamp = int(timestamp) if timestamp.isdigit() else 0
    sign = request.POST.get('sign', '')

    token = AccessToken.objects.filter(tokenid=code).first()
    if not token:
        raise SuspiciousOperation()

    service = token.service
    if service.name != client_id:
        raise SuspiciousOperation()
    elif token.expire_time < timezone.now():
        raise SuspiciousOperation()

    now = timezone.now()
    date = datetime.fromtimestamp(timestamp, timezone.utc)
    if abs((now - date).total_seconds()) >= 3:
        raise SuspiciousOperation()

    sign_server = hmac.new(str(service.secret_key),
                           str('%s%s' % (code, timestamp))).hexdigest()
    if not constant_time_compare(sign, sign_server):
        raise SuspiciousOperation()

    logger.info('token.delete', {'r': request, 'hide': True})
    token.delete()

    user = token.user
    profile = user.profile
    m = ServiceMap.objects.get(user=user, service=service)

    resp = {
        'uid': user.username,
        'sid': m.sid,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'gender': profile.gender,
        'birthday': date2str(profile.birthday),
        'flags': extract_flag(profile.flags),
        'facebook_id': profile.facebook_id,
        'twitter_id': profile.twitter_id,
        'kaist_id': profile.kaist_id,
        'kaist_info': profile.kaist_info,
        'kaist_info_time': date2str(profile.kaist_info_time),
        'sparcs_id': profile.sparcs_id
    }

    return HttpResponse(json.dumps(resp), content_type='application/json')


# /logout/
@csrf_exempt
def logout(request):
    if request.method != 'POST':
        raise SuspiciousOperation()

    client_id = request.POST.get('client_id', '')
    sid = request.POST.get('sid', '')
    timestamp = request.POST.get('timestamp', '0')
    timestamp = int(timestamp) if timestamp.isdigit() else 0
    redirect_uri = request.POST.get('redirect_uri', '')
    sign = request.POST.get('sign', '')

    service = Service.objects.filter(name=client_id).first()
    if not service:
        raise SuspiciousOperation()

    m = ServiceMap.objects.filter(sid=sid, service=service).first()
    if not m:
        return redirect(service.main_url)

    if not redirect_uri:
        redirect_uri = service.main_url
    validate = URLValidator()
    try:
        validate(redirect_uri)
    except:
        raise SuspiciousOperation()

    now = timezone.now()
    date = datetime.fromtimestamp(timestamp, timezone.utc)
    if abs((now - date).total_seconds()) >= 3:
        raise SuspiciousOperation()

    sign_server = hmac.new(str(service.secret_key),
                           str('%s%s%s' % (sid, redirect_uri, timestamp))).hexdigest()
    if not constant_time_compare(sign, sign_server):
        raise SuspiciousOperation()

    logger.info('logout', {'r': request})
    auth.logout(request)

    return redirect(redirect_uri)


# /point/
@csrf_exempt
@transaction.atmoic
def point(request):
    if request.method != 'POST':
        raise SuspiciousOperation()

    client_id = request.POST.get('client_id', '')
    sid = request.POST.get('sid', '')
    delta = request.POST.get('delta', '0')
    message = request.POST.get('message', '')
    lower_bound = request.POST.get('lower_bound', '-100000000')
    timestamp = request.POST.get('timestamp', '0')
    timestamp = int(timestamp) if timestamp.isdigit() else 0
    sign = request.POST.get('sign', '')

    service = Service.objects.filter(name=client_id).first()
    if not service:
        raise SuspiciousOperation()

    m = ServiceMap.objects.filter(sid=sid, service=service).first()
    if not m:
        raise SuspiciousOperation()

    try:
        delta = int(delta)
        lower_bound = int(lower_bound)
    except:
        raise SuspiciousOperation()

    now = timezone.now()
    profile = m.user.profile
    if delta != 0 and not message:
        raise SuspiciousOperation()
    elif delta != 0 and abs((now - profile.point_time)) < 5:
        raise SuspiciousOperation()

    date = datetime.fromtimestamp(timestamp, timezone.utc)
    if abs((now - date).total_seconds()) >= 3:
        raise SuspiciousOperation()

    sign_server = hmac.new(str(service.secret_key),
                           str('%s%s%s%s' % (sid, delta, lower_bound, timestamp))).hexdigest()
    if not constant_time_compare(sign, sign_server):
        raise SuspiciousOperation()

    is_test_app = service.scope == 'TEST'
    point = profile.point_test if is_test_app else profile.point
    modified = False

    if delta:
        if is_test_app:
            profile.point_test += delta
        else:
            profile.point += delta
        profile.point_time = timezone.now()
        profile.save()

        point += delta
        modified = True

        manager = m.user.point_logs
        if manager.count() >= 20:
            manager.order_by('time')[0].delete()
        PointLog(user=m.user, service=service, delta=delta,
                 point=profile.point, action=message).save()

    last_request = profile.point_time
    return HttpResponse(json.dumps({'point': point, 'modified': modified,
                                    'last_request': last_request}),
                                    content_type="application/json")


# /notice/
def notice(request):
    offset = request.GET.get('offset', '0')
    offset = int(offset) if offset.isdigit() else 0
    limit = request.GET.get('limit', '3')
    limit = int(limit) if limit.isdigit() else 0
    date_after = request.GET.get('date_after', '0')
    date_after = int(date_after) if date_after.isdigit() else 0

    if not date_after:
        date_after = timezone.now()
    else:
        date_after = datetime.fromtimestamp(date_after, timezone.utc)

    notices = Notice.objects.filter(valid_to__gt=date_after)[offset:offset+limit]

    notices_dict = map(lambda x: x.to_dict(), notices)
    return HttpResponse(json.dumps({'notices': notices_dict}), content_type="application/json")


# /email/
def email(request):
    if validate_email(request.GET.get('email', '')):
        return HttpResponse(status=200)
    return HttpResponse(status=400)


# /stats/
def stats(request):
    pass
