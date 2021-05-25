import logging
from urllib.parse import parse_qs, urljoin, urlparse

from django.conf import settings
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.core.backends import (
    anon_required, auth_fb_callback, auth_fb_init,
    auth_kaist_callback, auth_kaist_init, auth_tw_callback,
    auth_tw_init, get_clean_url, get_social_name,
)
from apps.core.constants import SocialConnectResult
from apps.core.models import Notice, Service


logger = logging.getLogger('sso.auth')
profile_logger = logging.getLogger('sso.profile')


def login_core(request, session_name, template_name, get_user_func):
    if 'next' in request.GET:
        request.session['next'] = request.GET['next']

    current_time = timezone.now()
    notice = Notice.objects.filter(
        valid_from__lte=current_time, valid_to__gt=current_time,
    ).first()

    query_dict = parse_qs(urlparse(
        request.session.get('next', '/'),
    ).query)
    service_name = query_dict.get('client_id', [''])[0]
    service = Service.objects.filter(name=service_name).first()

    ip = request.META.get('REMOTE_ADDR', '')
    show_internal = (
        ip.startswith('143.248.234.') or
        (service and service.scope == 'SPARCS')
    )

    if request.method == 'POST':
        user = get_user_func(request.POST)
        if user:
            request.session.pop('info_signup', None)
            auth.login(request, user)

            return redirect(get_clean_url(
                request.session.pop('next', '/'),
            ))

        request.session[session_name] = 1

    return render(request, template_name, {
        'notice': notice,
        'service': service.alias if service else '',
        'fail': request.session.pop(session_name, ''),
        'show_internal': show_internal,
        'kaist_enabled': settings.KAIST_APP_ENABLED,
    })


# /login/
@anon_required
def login(request):
    def get_user_func(post_dict):
        email = post_dict.get('email', 'null@sso.sparcs.org')
        password = post_dict.get('password', 'unknown')
        return auth.authenticate(
            request=request, email=email, password=password,
        )

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
        return auth.authenticate(
            request=request, ldap_id=ldap_id, ldap_pw=ldap_pw,
        )

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
def init(request, mode, site):
    if request.method != 'POST':
        return redirect('/')

    # disable login for authenticated user
    # disable connect / renew for non authenticated user
    is_authenticated = request.user.is_authenticated
    if (mode == 'LOGIN' and is_authenticated) or \
       (mode in ['CONN', 'RENEW'] and not is_authenticated):
        return redirect('/')

    # disable manual connect / renew for test user
    if mode in ['CONN', 'RENEW'] and request.user.profile.test_only:
        result_code = SocialConnectResult.TEST_ONLY
        return HttpResponseRedirect(f'/account/profile/?connect_site={site}&connect_result={result_code.name}')

    request.session['info_auth'] = {'mode': mode, 'type': site}
    callback_url = urljoin(settings.DOMAIN, '/account/callback/')

    if site == 'FB':
        url = auth_fb_init(callback_url)
    elif site == 'TW':
        url, token = auth_tw_init(callback_url)
        request.session['request_token'] = token
    elif site == 'KAIST':
        url, token = auth_kaist_init(callback_url)
        request.session['request_token'] = token
    return redirect(url)


# /callback/
@csrf_exempt
def callback(request):
    info_auth = request.session.pop('info_auth', None)
    if not info_auth:
        return redirect('/')

    mode, site = info_auth['mode'], info_auth['type']
    if site == 'FB':
        code = request.GET.get('code')
        callback_url = urljoin(settings.DOMAIN, '/account/callback/')
        profile, info = auth_fb_callback(code, callback_url)
    elif site == 'TW':
        tokens = request.session.get('request_token')
        verifier = request.GET.get('oauth_verifier')
        profile, info = auth_tw_callback(tokens, verifier)
    elif site == 'KAIST':
        token = request.session.get('request_token')
        iam_info = request.POST.get('result')
        profile, info, valid = auth_kaist_callback(token, iam_info)
        if not valid:
            return redirect('/')
    else:
        # Should not reach here!
        return redirect('/')

    uid = info['userid'] if info else 'unknown'
    logger.info('social', {
        'r': request,
        'hide': True,
        'extra': [
            ('type', get_social_name(site)),
            ('uid', uid),
        ],
    })
    user = profile.user if profile else None

    if mode == 'LOGIN':
        response = callback_login(request, site, user, info)
    elif mode == 'CONN':
        response = callback_conn(request, site, user, info)
    elif mode == 'RENEW':
        response = callback_renew(request, site, user, info)

    # TODO: Find out what this is for
    response.delete_cookie('SATHTOKEN')
    return response


# from /callback/
def callback_login(request, site, user, info):
    if not user and not info:
        request.session['result_login'] = 2
        return redirect('/account/login/')

    # no such user; go to signup page
    if not user:
        request.session['info_signup'] = {'type': site, 'profile': info}
        response = redirect('/account/signup/social/')
        return response

    user = auth.authenticate(request=request, user=user)
    # critical logic fail
    if not user:
        request.session['result_login'] = 2
        return redirect('/account/login/')

    # normal login
    request.session.pop('info_signup', None)
    if site == 'KAIST':
        user.profile.save_kaist_info(info)

    auth.login(request, user)
    nexturl = request.session.pop('next', '/')
    return redirect(get_clean_url(nexturl))


# from /callback/
def callback_conn(request, site, user, info):
    result_code = SocialConnectResult.CONNECT_SUCCESS
    profile = request.user.profile
    if not user and not info:
        result_code = SocialConnectResult.PERMISSION_NEEDED
    elif user:
        result_code = SocialConnectResult.ALREADY_CONNECTED
    elif site == 'FB' and not profile.facebook_id:
        profile.facebook_id = info['userid']
    elif site == 'TW' and not profile.twitter_id:
        profile.twitter_id = info['userid']
    elif site == 'KAIST' and not profile.kaist_id:
        profile.save_kaist_info(info)
    else:
        result_code = SocialConnectResult.SITE_INVALID

    profile.save()
    request.session['result_con'] = result_code.value

    log_msg = 'success' if result_code == SocialConnectResult.CONNECT_SUCCESS else 'fail'
    profile_logger.warning(f'social.connect.{log_msg}', {
        'r': request,
        'extra': [
            ('type', get_social_name(site)),
            ('uid', info['userid'] if info else 'unknown'),
        ],
    })
    return HttpResponseRedirect(f'/account/profile/?connect_site={site}&connect_result={result_code.name}')


# from /callback/
def callback_renew(request, site, user, info):
    if site != 'KAIST':
        result_code = SocialConnectResult.RENEW_UNNECESSARY
        return HttpResponseRedirect(f'/account/profile/?connect_site={site}&connect_result={result_code.name}')

    result_code = SocialConnectResult.CONNECT_SUCCESS
    profile = user.profile
    if profile.kaist_id != info['userid']:
        result_code = SocialConnectResult.KAIST_IDENTITY_MISMATCH
    else:
        user.profile.save_kaist_info(info)

    request.session['result_con'] = result_code.value

    log_msg = 'success' if result_code == SocialConnectResult.CONNECT_SUCCESS else 'fail'
    profile_logger.warning(f'social.update.{log_msg}', {
        'r': request,
        'extra': [
            ('type', get_social_name(site)),
            ('uid', info['userid'] if info else 'unknown'),
        ],
    })
    return HttpResponseRedirect(f'/account/profile/?connect_site={site}&connect_result={result_code.name}')
