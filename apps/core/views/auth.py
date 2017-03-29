from django.conf import settings
from django.contrib import auth
from django.shortcuts import render, redirect
from django.utils import timezone
from apps.core.backends import (
    auth_fb_init, auth_fb_callback,
    auth_tw_init, auth_tw_callback,
    auth_kaist_init, auth_kaist_callback,
    get_clean_url, get_social_name,
)
from apps.core.models import Notice, Service
from urllib.parse import urlparse, parse_qs
import logging


logger = logging.getLogger('sso.core.auth')
profile_logger = logging.getLogger('sso.profile')


# /login/
def login(request):
    if request.user.is_authenticated:
        return redirect('/')

    current_time = timezone.now()
    notice = Notice.objects.filter(valid_from__lte=current_time,
                                   valid_to__gt=current_time).first()

    if 'next' in request.GET:
        request.session['next'] = request.GET['next']

    query_dict = parse_qs(urlparse(request.session.get('next', '/')).query)
    service_name = query_dict.get('client_id', [''])[0]
    service = Service.objects.filter(name=service_name).first()
    service_alias = service.alias if service else ''

    if request.method == 'POST':
        email = request.POST.get('email', 'null@sso.sparcs.org')
        password = request.POST.get('password', 'unknown')
        user = auth.authenticate(request=request,
                                 email=email,
                                 password=password)
        if user:
            request.session.pop('info_signup', None)
            auth.login(request, user)

            nexturl = request.session.pop('next', '/')
            return redirect(get_clean_url(nexturl))

        request.session['result_login'] = 1

    context = {
        'notice': notice,
        'service': service_alias,
        'fail': request.session.pop('result_login', ''),
        'kaist_enabled': settings.KAIST_APP_ENABLED,
    }
    return render(request, 'account/login.html', context)


# /logout/
def logout(request):
    if request.method != 'POST' or not request.user.is_authenticated:
        return redirect('/')

    auth.logout(request)
    return render(request, 'account/logout.html')


# /login/{fb,tw,kaist}/, /connect/{fb,tw,kaist}/, /renew/kaist/
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
    type_str = get_social_name(type)
    logger.info('social.{}: id={}'.format(type_str, userid), {
        'r': request,
        'hide': True,
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
        user.profile.set_kaist_info(info)

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
        profile.set_kaist_info(info)
    else:
        return redirect('/account/profile/')

    profile.save()
    request.session['result_con'] = result_con

    userid = info['userid'] if info else 'unknown'
    type_str = get_social_name(type)
    if result_con == 0:
        profile_logger.warning('social.connect.success: type={},id={}'.format(
            type_str, userid), {'r': request})
    else:
        profile_logger.warning('social.connect.fail: type={},id={}'.format(
            type_str, userid), {'r': request})

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

    userid = info['userid'] if info else 'unknown'
    type_str = get_social_name(type)
    if result_con == 0:
        profile_logger.warning('social.update.success: type={},id={}'.format(
            type_str, userid), {'r': request})
    else:
        profile_logger.warning('social.fail.success: type={},id={}'.format(
            type_str, userid), {'r': request})

    return redirect('/account/profile/')
