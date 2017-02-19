from django.conf import settings
from django.contrib import auth
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils import timezone
from apps.core.backends import get_username, \
    init_fb, init_tw, auth_fb, auth_tw, auth_kaist
from apps.core.models import Notice, Service
from urlparse import urlparse, parse_qs
import logging


logger = logging.getLogger('sso.core.auth')
account_logger = logging.getLogger('sso.core.account')
profile_logger = logging.getLogger('sso.core.profile')


# /login/
def login(request):
    if request.user.is_authenticated():
        return redirect('/')

    current_time = timezone.now()
    notice = Notice.objects.filter(valid_from__lte=current_time,
                                   valid_to__gt=current_time).first()

    if 'next' in request.GET:
        request.session['next'] = request.GET['next']

    query_dict = parse_qs(urlparse(request.session.get('next', '/')).query)
    service = Service.objects.filter(name=query_dict.get('client_id', [''])[0]).first()
    srv_name = service.alias if service else ''

    if request.method == 'POST':
        email = request.POST.get('email', 'none')
        password = request.POST.get('password', 'asdf')

        username = get_username(email)
        user = auth.authenticate(username=username, password=password)
        if user and not user.is_active:
            logger.info('login.reject', {'r': request, 'uid': username})
            raise PermissionDenied()
        elif user:
            request.session.pop('info_signup', None)
            auth.login(request, user)
            logger.info('login.success', {'r': request})

            if not settings.DEBUG and user.is_staff:
                title = '[SPARCS SSO] Staff Login'
                message = 'time:%s; id:%s; ip:%s;'
                emails = map(lambda x: x[1], settings.ADMINS)
                time = timezone.now()
                ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                send_mail(title, '', 'noreply@sso.sparcs.org', emails,
                          html_message=message % (time, username, ip))

            if user.profile.activate():
                account_logger.warning('activate', {'r': request})

            nexturl = request.session.pop('next', '/')
            return redirect(nexturl)
        else:
            logger.info('login.fail', {'r': request, 'uid': username})
            request.session['result_login'] = 1

    context = {
        'notice': notice,
        'service': srv_name,
        'fail': request.session.pop('result_login', ''),
        'kaist_enabled': settings.KAIST_APP_ENABLED,
    }
    return render(request, 'account/login.html', context)


# /logout/
def logout(request):
    if request.method != 'POST' or not request.user.is_authenticated():
        return redirect('/')

    logger.info('logout', {'r': request})
    auth.logout(request)
    return render(request, 'account/logout.html')


# /login/{fb,tw,kaist}/, /connect/{fb,tw,kaist}/, /renew/kaist/
def init(request, mode, type):
    is_authed = request.user.is_authenticated()
    if (mode == 'LOGIN' and is_authed) or \
       (mode == 'CONN' and not is_authed) or \
       (mode == 'RENEW' and not is_authed):
        return redirect('/')

    method = request.method
    if (mode == 'CONN' and method != 'POST') or \
       (mode == 'RENEW' and method != 'POST'):
        return redirect('/account/profile/')

    if is_authed and request.user.profile.test_only and \
            (mode == 'CONN' or mode == 'RENEW'):
        return redirect('/account/profile/')

    request.session['info_auth'] = {'mode': mode, 'type': type}
    callback_url = request.build_absolute_uri('/account/callback/')

    url = ''
    if type == 'FB':
        url = init_fb(callback_url)
    elif type == 'TW':
        url, request.session['request_token'] = init_tw(callback_url)
    elif type == 'KAIST':
        url = 'https://ksso.kaist.ac.kr/iamps/requestLogin.do'
    return redirect(url)


# /callback/
def callback(request):
    auth = request.session.pop('info_auth', None)
    if not auth:
        return redirect('/')

    mode, type = auth['mode'], auth['type']
    user, profile = None, None
    if type == 'FB':
        code = request.GET.get('code')
        callback_url = request.build_absolute_uri('/account/callback/')
        profile, info = auth_fb(code, callback_url)
    elif type == 'TW':
        tokens = request.session.get('request_token')
        verifier = request.GET.get('oauth_verifier')
        profile, info = auth_tw(tokens, verifier)
    elif type == 'KAIST':
        token = request.COOKIES.get('SATHTOKEN')
        profile, info = auth_kaist(token)

    userid = info['userid'] if info else 'none'
    logger.info('%s: id=%s' % (type.lower(), userid), {'r': request, 'hide': True})
    user = profile.user if profile else None

    if mode == 'LOGIN':
        response = callback_login(request, type, user, info)
    elif mode == 'CONN':
        response = callback_conn(request, type, user, info)
    elif mode == 'RENEW':
        response = callback_renew(request, type, user, info)

    response.delete_cookie('SATHTOKEN')
    return response


# from /callback/
def callback_login(request, type, user, info):
    if not user and not info:
        request.session['result_login'] = 2
        return redirect('/account/login/')

    if not user:
        request.session['info_signup'] = {'type': type, 'profile': info}
        response = redirect('/account/signup/social/')
        response.delete_cookie('SATHTOKEN')
        return response

    request.session.pop('info_signup', None)
    if type == 'KAIST':
        user.profile.set_kaist_info(info)

    user.backend = 'django.contrib.auth.backends.ModelBackend'
    auth.login(request, user)
    logger.info('login.success', {'r': request})

    if user.profile.activate():
        account_logger.warning('activate', {'r': request})

    nexturl = request.session.pop('next', '/')
    return redirect(nexturl)


# from /callback/
def callback_conn(request, type, user, info):
    result_con = 0
    profile = request.user.profile
    if not user and not info:
        result_con = 3
    elif user:
        result_con = 1
    elif type == 'FB' and not profile.facebook_id:
        profile.facebook_id = info['userid']
    elif type == 'TW' and not profile.twitter_id:
        profile.twitter_id = info['userid']
    elif type == 'KAIST' and not profile.kaist_id:
        profile.set_kaist_info(info)
    else:
        return redirect('/account/profile/')

    profile.save()
    request.session['result_con'] = result_con

    userid = info['userid'] if info else 'none'
    if result_con == 0:
        profile_logger.warning('connect.success: type=%s,id=%s'
                               % (type.lower(), userid), {'r': request})
    else:
        profile_logger.warning('connect.fail: type=%s,id=%s'
                               % (type.lower(), userid), {'r': request})

    return redirect('/account/profile/')


# from /callback/
def callback_renew(request, type, user, info):
    if type != 'KAIST':
        return redirect('/account/profile/')

    result_con = 0
    profile = user.profile
    if profile.kaist_id != info['userid']:
        result_con = 2
    else:
        user.profile.set_kaist_info(info)

    request.session['result_con'] = result_con
    if result_con == 0:
        profile_logger.warning('renew.success: type=%s,id=%s'
                               % (type.lower(), info['userid']), {'r': request})
    else:
        profile_logger.warning('renew.fail: type=%s,id=%s'
                               % (type.lower(), info['userid']), {'r': request})

    return redirect('/account/profile/')
