import datetime
import logging
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.contrib import auth
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.backends import (
    anon_required, auth_fb_callback, auth_fb_init,
    auth_kaist_callback, auth_kaist_init, auth_tw_callback,
    auth_tw_init, get_clean_url, get_social_name,
    validate_recaptcha,
)
from apps.core.models import LoginFailureLog, Notice, Service


logger = logging.getLogger('sso.auth')
profile_logger = logging.getLogger('sso.profile')


def login_core(request, session_name, template_name, get_user_func):
    if 'next' in request.GET:
        request.session['next'] = request.GET['next']

    current_time = timezone.now()
    notice = Notice.objects.filter(
        valid_from__lte=current_time, valid_to__gt=current_time,
    ).first()

    query_dict = parse_qs(urlparse(request.session.get('next', '/')).query)
    service_name = query_dict.get('client_id', [''])[0]
    service = Service.objects.filter(name=service_name).first()

    ip = request.META.get('REMOTE_ADDR', '')
    show_internal = (
        ip.startswith('143.248.234.') or
        (service and service.scope == 'SPARCS')
    )

    login_failure_timerange = datetime.timedelta(
        minutes=settings.RECAPTCHA_LOGIN_FAILURE_TIME_RANGE)
    last_login_failures = LoginFailureLog.objects.filter(
        ip=ip, time__gte=(current_time - login_failure_timerange))

    show_recaptcha = last_login_failures.count() >= settings.RECAPTCHA_LOGIN_FAILURE_COUNT
    if request.method == 'POST':
        if show_recaptcha:
            captcha_data = request.POST.get('g-recaptcha-response', '')
            captcha_success = validate_recaptcha(captcha_data, settings.RECAPTCHA_CHECKBOX_SECRET)
        else:
            captcha_success = True

        user, attempted_username = get_user_func(request.POST)
        if user and captcha_success:
            request.session.pop('info_signup', None)
            auth.login(request, user)

            return redirect(get_clean_url(
                request.session.pop('next', '/'),
            ))

        request.session[session_name] = 3 if user else 1
        if ip:
            log_failure = LoginFailureLog()
            log_failure.ip = ip
            log_failure.username = attempted_username
            log_failure.save()

    return render(request, template_name, {
        'notice': notice,
        'service': service.alias if service else '',
        'fail': request.session.pop(session_name, ''),
        'show_internal': show_internal,
        'kaist_enabled': settings.KAIST_APP_ENABLED,
        'recaptcha_sitekey': settings.RECAPTCHA_CHECKBOX_SITEKEY if show_recaptcha else '',
    })


# /login/
@anon_required
def login(request):
    def get_user_func(post_dict):
        email = post_dict.get('email', 'null@sso.sparcs.org')
        password = post_dict.get('password', 'unknown')
        user = auth.authenticate(request=request, email=email, password=password)
        return user, email

    return login_core(
        request, 'result_login',
        'account/login/main.html', get_user_func,
    )


# /login/internal/
@anon_required
def login_internal(request):
    def get_user_func(post_dict):
        ldap_id = post_dict.get('ldap-id', 'unknown')
        ldap_pw = post_dict.get('ldap-pw', 'unknown')
        user = auth.authenticate(request=request, ldap_id=ldap_id, ldap_pw=ldap_pw)
        return user, ldap_id

    return login_core(
        request, 'result_login_internal',
        'account/login/internal.html', get_user_func,
    )


# /logout/
@require_POST
def logout(request):
    if not request.user.is_authenticated:
        return redirect('/')

    auth.logout(request)
    return render(request, 'account/logout.html')


# /login/{fb,tw,kaist}/, /connect/{fb,tw,kaist}/, /renew/kaist/
@require_POST
def init(request, mode, type):
    if request.method != 'POST':
        return redirect('/')

    # disable login for authed user
    # disable connect / renew for non authed user
    is_authed = request.user.is_authenticated
    if (mode == 'LOGIN' and is_authed) or \
       (mode in ['CONN', 'RENEW'] and not is_authed):
        return redirect('/')

    # disable manual connect / renew for test user
    if mode in ['CONN', 'RENEW'] and request.user.profile.test_only:
        return redirect('/account/profile/')

    request.session['info_auth'] = {'mode': mode, 'type': type}
    callback_url = request.build_absolute_uri('/account/callback/')

    if type == 'FB':
        url = auth_fb_init(callback_url)
    elif type == 'TW':
        url, token = auth_tw_init(callback_url)
        request.session['request_token'] = token
    elif type == 'KAIST':
        url = auth_kaist_init()
    return redirect(url)


# /callback/
def callback(request):
    auth = request.session.pop('info_auth', None)
    if not auth:
        return redirect('/')

    mode, type = auth['mode'], auth['type']
    if type == 'FB':
        code = request.GET.get('code')
        callback_url = request.build_absolute_uri('/account/callback/')
        profile, info = auth_fb_callback(code, callback_url)
    elif type == 'TW':
        tokens = request.session.get('request_token')
        verifier = request.GET.get('oauth_verifier')
        profile, info = auth_tw_callback(tokens, verifier)
    elif type == 'KAIST':
        token = request.COOKIES.get('SATHTOKEN')
        profile, info = auth_kaist_callback(token)

    userid = info['userid'] if info else 'unknown'
    logger.info('social', {
        'r': request,
        'hide': True,
        'extra': [
            ('type', get_social_name(type)),
            ('uid', userid),
        ],
    })
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

    # no such user; go to signup page
    if not user:
        request.session['info_signup'] = {'type': type, 'profile': info}
        response = redirect('/account/signup/social/')
        return response

    user = auth.authenticate(request=request, user=user)
    # critical logic fail
    if not user:
        request.session['result_login'] = 2
        return redirect('/account/login/')

    # normal login
    request.session.pop('info_signup', None)
    if type == 'KAIST':
        user.profile.save_kaist_info(info)

    auth.login(request, user)
    nexturl = request.session.pop('next', '/')
    return redirect(get_clean_url(nexturl))


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
        profile.save_kaist_info(info)
    else:
        return redirect('/account/profile/')

    profile.save()
    request.session['result_con'] = result_con

    log_msg = 'success' if result_con == 0 else 'fail'
    profile_logger.warning(f'social.connect.{log_msg}', {
        'r': request,
        'extra': [
            ('type', get_social_name(type)),
            ('uid', info['userid'] if info else 'unknown'),
        ],
    })
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
        user.profile.save_kaist_info(info)

    request.session['result_con'] = result_con

    log_msg = 'success' if result_con == 0 else 'fail'
    profile_logger.warning(f'social.update.{log_msg}', {
        'r': request,
        'extra': [
            ('type', get_social_name(type)),
            ('uid', info['userid'] if info else 'unknown'),
        ],
    })
    return redirect('/account/profile/')
