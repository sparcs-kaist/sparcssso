from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.core.validators import URLValidator
from django.contrib import auth
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from apps.core.backends import service_register, validate_email
from apps.core.models import Notice, Service, ServiceMap, AccessToken, PointLog, Statistic
from datetime import datetime, timedelta
from secrets import token_hex
from urllib.parse import urlencode
import hmac
import json
import logging


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


def get_hash(key, msg):
    return hmac.new(key.encode(), msg.encode()).hexdigest()


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
        return render(request, 'api/denied.html',
                      {'reason': reason, 'alias': service.alias})

    token = AccessToken.objects.filter(user=user, service=service).first()
    if token:
        logger.info('token.delete', {'r': request, 'hide': True})
        token.delete()

    m = ServiceMap.objects.filter(user=user, service=service).first()
    if not m or m.unregister_time:
        result = service_register(user, service)
        if result:
            profile_logger.info(
                f'register.success: app={service.name}',
                {'r': request},
            )
        else:
            left = service.cooltime - (timezone.now() - m.unregister_time).days
            profile_logger.warning(
                f'register.fail: app={service.name}',
                {'r': request},
            )
            return render(request, 'api/cooltime.html', {
                'service': service,
                'left': left,
            })

    while True:
        tokenid = token_hex(10)
        if not AccessToken.objects.filter(tokenid=tokenid, service=service).count():
            break

    token = AccessToken(tokenid=tokenid, user=user, service=service,
                        expire_time=timezone.now() + timedelta(seconds=10))
    token.save()
    logger.info(f'token.create: app={client_id}', {'r': request})

    args = {'code': token.tokenid, 'state': state}
    return redirect(service.login_callback_url + '?' + urlencode(args))


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
    if abs((now - date).total_seconds()) >= 10:
        raise SuspiciousOperation()

    sign_server = get_hash(service.secret_key, '{}{}'.format(code, timestamp))
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
def logout(request):
    client_id = request.GET.get('client_id', '')
    sid = request.GET.get('sid', '')
    timestamp = request.GET.get('timestamp', '0')
    timestamp = int(timestamp) if timestamp.isdigit() else 0
    redirect_uri = request.GET.get('redirect_uri', '')
    sign = request.GET.get('sign', '')

    service = Service.objects.filter(name=client_id).first()
    if not service:
        raise SuspiciousOperation()

    m = ServiceMap.objects.filter(sid=sid, service=service).first()
    if not m:
        return redirect(service.main_url)

    if redirect_uri:
        validate = URLValidator()
        try:
            validate(redirect_uri)
        except:
            raise SuspiciousOperation()

    now = timezone.now()
    date = datetime.fromtimestamp(timestamp, timezone.utc)
    if abs((now - date).total_seconds()) >= 30:
        raise SuspiciousOperation()

    sign_server = get_hash(service.secret_key,
                           '{}{}{}'.format(sid, redirect_uri, timestamp))
    if not constant_time_compare(sign, sign_server):
        raise SuspiciousOperation()

    if request.user and request.user.is_authenticated:
        logger.info('logout', {'r': request})
        auth.logout(request)

    if not redirect_uri:
        redirect_uri = service.main_url
    return redirect(redirect_uri)


# /point/
@csrf_exempt
@transaction.atomic
def point(request):
    if request.method != 'POST':
        raise SuspiciousOperation()

    client_id = request.POST.get('client_id', '')
    sid = request.POST.get('sid', '')
    delta = request.POST.get('delta', '0')
    message = request.POST.get('message', '')
    lower_bound = request.POST.get('lower_bound', '0')
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

    date = datetime.fromtimestamp(timestamp, timezone.utc)
    if abs((now - date).total_seconds()) >= 5:
        raise SuspiciousOperation()

    sign_server = get_hash(service.secret_key,
                           '{}{}{}{}'.format(sid, delta, lower_bound, timestamp))
    if not constant_time_compare(sign, sign_server):
        raise SuspiciousOperation()

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

    notices = Notice.objects.filter(valid_to__gt=date_after)[offset:offset + limit]
    notices_dict = list(map(lambda x: x.to_dict(), notices))
    return HttpResponse(
        json.dumps({'notices': notices_dict}),
        content_type='application/json',
    )


# /email/
def email(request):
    if validate_email(request.GET.get('email', ''), request.GET.get('exclude', '')):
        return HttpResponse(status=200)
    return HttpResponse(status=400)


# /stats/
def stats(request):
    level = 0
    if request.user.is_authenticated:
        if request.user.is_staff:
            level = 2
        elif request.user.profile.sparcs_id:
            level = 1

    client_ids = request.GET.get('client_ids', '').split(',')
    client_list = list(filter(None, map(lambda x:
        Service.objects.filter(name=x).first(), client_ids)))
    if not client_list:
        client_list = Service.objects.all()

    if level > 0:
        client_list = filter(lambda x: x.scope != 'TEST', client_list)
    elif level == 0:
        client_list = filter(lambda x: x.scope == 'PUBLIC', client_list)

    today = timezone.localtime(timezone.now())\
        .replace(hour=0, minute=0, second=0, microsecond=0)
    start_date, end_date = None, None
    try:
        start_date = parse_date(request.GET.get('date_from', ''))
    except:
        pass

    if not start_date:
        start_date = today

    try:
        end_date = parse_date(request.GET.get('date_to', ''))
    except:
        pass

    if not end_date:
        end_date = today.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

    raw_stats = Statistic.objects.filter(
        time__gte=start_date, time__lte=end_date
    )

    stats = {}
    for client in client_list:
        stat = {'alias': client.alias, 'data': {}}
        for raw_stat in raw_stats:
            raw_data = json.loads(raw_stat.data)

            if client.name not in raw_data:
                continue

            data = {}
            raw_data = raw_data[client.name]
            if level == 0:
                data['account'] = {}
                data['account']['all'] = raw_data['account']['all']
                data['account']['kaist'] = raw_data['account']['kaist']
            elif level == 1:
                data['account'] = raw_data['account']
                data['gender'] = raw_data['gender']
                data['birth_year'] = raw_data['birth_year']
            elif level == 2:
                data = raw_data

            stat['data'][raw_stat.time.isoformat()] = data
        stats[client.name] = stat

    return HttpResponse(
        json.dumps({'stats': stats}),
        content_type='application/json',
    )
