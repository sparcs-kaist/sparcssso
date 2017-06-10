import hmac
import json
import logging
import re
import time
from datetime import datetime, timedelta
from secrets import token_hex
from urllib.parse import urlencode

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.core.validators import URLValidator
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt

from ...core.backends import service_register, validate_email
from ...core.models import (
    AccessToken, Notice, PointLog, Service, ServiceMap, Statistic,
)


logger = logging.getLogger('sso.service')
TIMEOUT = 60


def date2str(obj):
    if obj:
        return obj.isoformat()
    return ''


def str2date(string, default):
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', string)
    if not m:
        return default
    return datetime(
        int(m.group(1)), int(m.group(2)), int(m.group(3)),
        0, 0, 0, tzinfo=timezone.get_current_timezone(),
    )


def extract_flag(flags):
    result = []
    if flags['test']:
        result.append('TEST')
    if flags['sparcs']:
        result.append('SPARCS')
    return result


def check_sign(data, keys):
    extracted = list(map(lambda k: data.get(k, ''), keys))

    client_id = data.get('client_id', '')
    service = Service.objects.filter(name=client_id).first()
    if not service:
        raise SuspiciousOperation('INVALID_SERVICE')

    timestamp = data.get('timestamp', '0')
    timestamp = int(timestamp) if timestamp.isdigit() else 0

    sign = data.get('sign', '')

    if abs(time.time() - timestamp) >= TIMEOUT:
        raise SuspiciousOperation('INALID_TIMESTAMP')

    sign_server = hmac.new(
        service.secret_key.encode(),
        (''.join(extracted) + str(timestamp)).encode(),
    ).hexdigest()
    if not constant_time_compare(sign, sign_server):
        raise SuspiciousOperation('INVALID_SIGN')

    return service, extracted, timestamp


# /token/require/
@login_required
def token_require(request):
    client_id = request.GET.get('client_id', '')
    state = request.GET.get('state', '')

    service = Service.objects.filter(name=client_id).first()
    if not service:
        raise SuspiciousOperation('INVALID_SERVICE')

    if len(state) < 8:
        raise SuspiciousOperation('INVALID_STATE')

    user = request.user
    profile = user.profile
    flags = user.profile.flags

    reason = 0
    if flags['sysop']:
        reason = 1
    elif service.scope == 'SPARCS' and not flags['sparcs']:
        reason = 2
    elif service.scope == 'TEST' and not flags['test']:
        reason = 3
    elif service.scope != 'TEST' and flags['test-only']:
        reason = 4
    elif not (profile.email_authed or profile.facebook_id or
              profile.twitter_id or profile.kaist_id):
        reason = 5

    if reason:
        return render(request, 'api/denied.html', {
            'reason': reason,
            'alias': service.alias,
        })

    AccessToken.objects.filter(user=user, service=service).delete()
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if not m or m.unregister_time:
        m_new = service_register(user, service)
        log_msg = 'success' if m_new else 'fail'
        logger.warning(f'register.{log_msg}', {
            'r': request,
            'extra': [
                ('app', service.name),
                ('sid', m_new.sid if m_new else ''),
            ],
        })
        if not m_new:
            left = service.cooltime - (timezone.now() - m.unregister_time).days
            return render(request, 'api/cooltime.html', {
                'service': service,
                'left': left,
            })

    while True:
        tokenid = token_hex(10)
        if not AccessToken.objects.filter(tokenid=tokenid).count():
            break

    token = AccessToken(
        tokenid=tokenid, user=user, service=service,
        expire_time=timezone.now() + timedelta(seconds=TIMEOUT),
    )
    token.save()
    logger.info('login.try', {
        'r': request,
        'hide': True,
        'extra': [('app', client_id)],
    })

    return redirect(service.login_callback_url + '?' + urlencode({
        'code': token.tokenid,
        'state': state,
    }))


# /token/info/
@csrf_exempt
def token_info(request):
    if request.method != 'POST':
        raise SuspiciousOperation('INVALID_METHOD')

    service, [code], timestamp = check_sign(
        request.POST, ['code'],
    )

    token = AccessToken.objects.filter(tokenid=code).first()
    if not token:
        raise SuspiciousOperation('INVALID_CODE')
    elif token.service.name != service.name:
        raise SuspiciousOperation('TOKEN_SERVICE_MISMATCH')
    elif token.expire_time < timezone.now():
        raise SuspiciousOperation('TOKEN_EXPIRED')

    logger.info('login.done', {
        'r': request,
        'uid': token.user.username,
        'extra': [('app', service.name)],
    })
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
        'sparcs_id': profile.sparcs_id,
    }

    return HttpResponse(json.dumps(resp), content_type='application/json')


# /logout/
def logout(request):
    service, [sid, redirect_uri], timestamp = check_sign(
        request.GET, ['sid', 'redirect_uri'],
    )

    m = ServiceMap.objects.filter(sid=sid, service=service).first()
    if not m:
        raise SuspiciousOperation('INVALID_CALL')

    if redirect_uri:
        validate = URLValidator()
        try:
            validate(redirect_uri)
        except:
            raise SuspiciousOperation('INVALID_URL')
    else:
        redirect_uri = service.main_url

    if request.user and request.user.is_authenticated:
        logger.info('logout', {
            'r': request,
            'extra': [
                ('app', service.name),
                ('redirect', redirect_uri),
            ],
        })
        auth.logout(request)
    return redirect(redirect_uri)


# /point/
@csrf_exempt
@transaction.atomic
def point(request):
    if request.method != 'POST':
        raise SuspiciousOperation('INVALID_METHOD')

    service, [sid, delta, message, lower_bound], timestamp = check_sign(
        request.POST, ['sid', 'delta', 'message', 'lower_bound'],
    )

    m = ServiceMap.objects.filter(sid=sid, service=service).first()
    if not m:
        raise SuspiciousOperation('INVALID_CALL')

    try:
        delta = 0 if not delta else int(delta)
        lower_bound = 0 if not lower_bound else int(lower_bound)
    except:
        raise SuspiciousOperation('INVALID_TYPE')

    if delta != 0 and not message:
        raise SuspiciousOperation('INVALID_MESSAGE')

    profile = m.user.profile
    is_test_app = service.scope == 'TEST'
    point = profile.point_test if is_test_app else profile.point
    modified = False

    if delta and point >= lower_bound:
        if is_test_app:
            profile.point_test += delta
        else:
            profile.point += delta
        profile.save()

        point += delta
        modified = True

        manager = m.user.point_logs
        if manager.count() >= 20:
            manager.order_by('time')[0].delete()

        logger.info('point', {
            'r': request,
            'uid': m.user.username,
            'hide': True,
            'extra': [
                ('app', service.name),
                ('delta', delta),
            ],
        })
        PointLog(user=m.user, service=service, delta=delta,
                 point=profile.point, action=message).save()

    return HttpResponse(
        json.dumps({'point': point, 'modified': modified}),
        content_type='application/json',
    )


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

    notices = Notice.objects.filter(valid_to__gt=date_after)
    notices = notices[offset:offset + limit]
    notices_dict = list(map(lambda x: x.to_dict(), notices))
    return HttpResponse(
        json.dumps({'notices': notices_dict}),
        content_type='application/json',
    )


# /email/
def email(request):
    email = request.GET.get('email', '')
    exclude = request.GET.get('exclude', '')
    if validate_email(email, exclude):
        return HttpResponse(status=200)
    return HttpResponse(status=400)


# /stats/
def stats(request):
    def filter_data(raw_data, level):
        if level == 0:
            return {
                'account': {
                    'all': raw_data['account']['all'],
                },
            }
        elif level == 1:
            return {
                'account': raw_data['account'],
                'gender': raw_data['gender'],
                'birth_year': raw_data['birth_year'],
            }
        elif level == 2:
            return raw_data
        return {}

    if not request.user.is_authenticated:
        level = 0
    elif request.user.profile.sparcs_id:
        level = 1
    elif request.user.is_staff:
        level = 2

    client_ids = list(filter(
        None, request.GET.get('client_ids', '').split(','),
    ))

    today = timezone.now().replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    start_date = str2date(request.GET.get('date_from', ''), today)
    end_date = str2date(request.GET.get('date_to', ''), today).replace(
        hour=23, minute=59, second=59, microsecond=999999,
    )
    day_diff = (end_date - start_date).days
    if level < 2 and day_diff > 60:
        start_date += timedelta(days=day_diff - 60)

    raw_stats = list(map(
        lambda x: (json.loads(x.data), x.time),
        Statistic.objects.filter(
            time__gte=start_date, time__lte=end_date,
        ),
    ))

    stats = {}
    if len(client_ids) == 0 or client_ids:
        client_ids = set()
        for raw_stat_data, _ in raw_stats:
            client_ids.update(raw_stat_data.keys())
        client_ids = list(client_ids)

    for client_id in client_ids:
        if not client_id:
            continue
        elif client_id.startswith('test'):
            continue
        elif level == 0 and client_id.startswith('sparcs'):
            continue

        client = Service.objects.filter(name=client_id).first()
        alias = client.alias if client else client_id
        stat = {'alias': alias, 'data': {}}
        for raw_stat_data, stat_time in raw_stats:
            if client_id not in raw_stat_data:
                continue

            stat['data'][stat_time.isoformat()] = filter_data(
                raw_stat_data[client_id], level,
            )
        stats[client_id] = stat

    return HttpResponse(
        json.dumps({'level': level, 'stats': stats}),
        content_type='application/json',
    )
