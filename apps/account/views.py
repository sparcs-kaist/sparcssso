# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone, translation
from apps.account.backends import give_email_auth_token, give_reset_pw_token, \
        get_username, validate_email, signup_backend, authenticate_fb, \
        authenticate_tw, authenticate_kaist, tw_client, tw_request_url, tw_auth_url
from apps.account.models import EmailAuthToken, ResetPWToken, Notice
from apps.account.forms import UserForm, UserProfileForm
from apps.oauth.models import Service, ServiceMap
import cgi
import datetime
import logging
import urllib


logger = logging.getLogger('sso.account')


# /login/{fb,tw,kaist}/, /connect/{fb,tw,kaist}/
def auth_init(request, mode, type):
    is_authed = request.user.is_authenticated()
    if (mode == 'LOGIN' and is_authed) or \
       (mode == 'CONN' and not is_authed):
        return redirect('/')

    if mode == 'CONN' and request.method != 'POST':
        raise SuspiciousOperation()

    request.session['info_auth'] = {'mode': mode, 'type': type}

    url = ''
    if type == 'FB':
        args = {
            'client_id': settings.FACEBOOK_APP_ID,
            'scope': 'email',
            'redirect_uri': request.build_absolute_uri('/account/callback/'),
        }
        url = 'https://www.facebook.com/dialog/oauth?' + urllib.urlencode(args)
    elif type == 'TW':
        body = 'oauth_callback=' + request.build_absolute_uri('/account/callback/')
        resp, content = tw_client.request(tw_request_url, 'POST', body)

        request.session['request_token'] = dict(cgi.parse_qsl(content))
        url = '%s?oauth_token=%s' % (tw_auth_url, request.session
                                     ['request_token']['oauth_token'])
    elif type == 'KAIST':
        url = 'https://ksso.kaist.ac.kr/iamps/requestLogin.do'

    return redirect(url)


# /main/
def main(request):
    current_time = timezone.now()
    services = Service.objects.filter(is_public=True)
    notice = Notice.objects.filter(valid_from__lte=current_time,\
        valid_to__gt=current_time).first()

    return render(request, 'main.html', {'services': services, 'notice': notice})


# /lang/
def lang(request, code):
    if code not in ['en', 'ko']:
        return redirect('/')

    translation.activate(code)
    request.session[translation.LANGUAGE_SESSION_KEY] = code
    return redirect(request.META.get('HTTP_REFERER', '/'))


# /credits/
def credits(request):
    return render(request, 'credits.html')


# /terms/
def terms(request):
    return render(request, 'terms.html')


# /privacy/
def privacy(request):
    return render(request, 'privacy.html')


# /doc/dev/
def doc_dev(request):
    u = request.user
    if not u.is_authenticated() or \
        (not u.is_staff and not u.profile.is_for_test and not u.profile.sparcs_id):
        return redirect('/')
    return render(request, 'doc.dev.html')


# /doc/sysop/
def doc_sysop(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        return redirect('/')
    return render(request, 'doc.sysop.html')


# /login/
def login(request):
    if request.user.is_authenticated():
        return redirect('/')

    current_time = timezone.now()
    notice = Notice.objects.filter(valid_from__lte=current_time,\
        valid_to__gt=current_time).first()

    if 'next' in request.GET:
        request.session['next'] = request.GET['next']

    if request.method == 'POST':
        email = request.POST.get('email', 'none')
        password = request.POST.get('password', 'asdf')

        username = get_username(email)

        user = auth.authenticate(username=username, password=password)
        if user is None or not user.is_active:
            logger.info('login.fail: authentication error', request)
            return render(request, 'account/login.html', {'fail': True, 'notice': notice})
        elif not user.profile.email_authed:
            request.session['info_user'] = user.id
            logger.info('login.fail: email is not authenticated, email=%s' % user.email, request)
            return redirect('/account/auth/email/')
        else:
            request.session.pop('info_user', None)
            request.session.pop('info_signup', None)
            auth.login(request, user)
            logger.info('login.success', request)

            if user.profile.expire_time:
                user.profile.expire_time = None
                user.profile.save()
                logger.warning('activate', request)

            nexturl = request.session.pop('next', '/')
            return redirect(nexturl)

    return render(request, 'account/login.html', {'notice': notice})


# /logout/
def logout(request):
    if not request.user.is_authenticated():
        return redirect('/')

    logger.info('logout', request)
    auth.logout(request)
    return render(request, 'account/logout.html')


# /auth/email/
def auth_email_resend(request):
    userid = request.session.get('info_user', None)
    if not userid:
        return redirect('/')

    user = User.objects.get(id=userid)

    if request.method == 'POST':
        if user.profile.email_authed:
            return redirect('/')

        give_email_auth_token(user)
        request.session.pop('info_user', None)
        logger.info('auth.email.resend: email=%s' % user.email, request)
        return render(request, 'account/auth-email/sent.html', {'email': user.email})

    return render(request, 'account/auth-email/send.html', {'email': user.email})


# /auth/email/<tokenid>
def auth_email(request, tokenid):
    token = EmailAuthToken.objects.filter(tokenid=tokenid).first()
    if not token:
        return render(request, 'account/auth-email/fail.html')
    user = token.user

    if token.expire_time < timezone.now():
        token.delete()
        logger.warning('auth.email.fail: expired token, email=%s' % token.user.email, request)
        return render(request, 'account/auth-email/fail.html')

    user.profile.email_authed = True
    user.profile.save()
    token.delete()
    logger.info('auth.email.success: username=%s, email=%s' % (user.username, user.email), request)
    return render(request, 'account/auth-email/success.html')


# /profile/
@login_required
def profile(request):
    user = request.user
    profile = user.profile

    success = False
    result_con = request.session.pop('result_con', -1)
    if request.method == 'POST':
        user_f = UserForm(request.POST)
        profile_f = UserProfileForm(request.POST, instance=profile)

        if user_f.is_valid() and profile_f.is_valid():
            user.first_name = user_f.cleaned_data['first_name']
            user.last_name = user_f.cleaned_data['last_name']
            user.save()

            profile = profile_f.save()
            success = True
            logger.info('profile.modify.success', request)
        else:
            logger.warning('profile.modify.fail', request)

    return render(request, 'account/profile.html',
                  {'user': user, 'profile': profile,
                   'success': success, 'result_con': result_con})


# /disconnect/{fb,tw}/
@login_required
def disconnect(request, type):
    if request.method != 'POST':
        raise SuspiciousOperation()

    profile = request.user.profile
    if type == 'FB':
        profile.facebook_id = ''
    elif type == 'TW':
        profile.twitter_id = ''
    profile.save()

    request.session['result_con'] = 5
    logger.info('profile.disconnect: type=%s' % type, request)
    return redirect('/account/profile/')


# /deactivate/
@login_required
def deactivate(request):
    maps = ServiceMap.objects.filter(user=request.user, unregister_time=None)
    ok = len(maps) == 0
    fail = False

    if request.method == 'POST' and ok:
        pw = request.POST.get('password', '')
        if check_password(pw, request.user.password):
            profile = request.user.profile
            profile.expire_time = timezone.now() + datetime.timedelta(days=60)
            profile.save()

            logger.warning('deactivate.success', request)
            return redirect('/account/logout/')

        fail = True
        logger.warning('deactivate.fail', request)

    return render(request, 'account/deactivate.html', {'ok': ok, 'fail': fail})


# /password/change/
@login_required
def password_change(request):
    user = request.user

    fail = False
    if request.method == 'POST':
        oldpw = request.POST.get('oldpassword', '')
        newpw = request.POST.get('password', 'P@55w0rd!#$')

        if check_password(oldpw, user.password):
            user.password = make_password(newpw)
            user.save()
            logger.warning('pw.change.success', request)
            return redirect('/account/login')

        fail = True
        logger.warning('pw.change.fail', request)

    return render(request, 'account/pw-change.html', {'user': user, 'fail': fail})


# /password/reset/
def password_reset_email(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        user = User.objects.filter(email=email).first()
        if not user:
            return render(request, 'account/pw-reset/send.html', {'fail': True, 'email': email})

        give_reset_pw_token(user)
        logger.warning('pw.reset.send: email=%s' % email, request)
        return render(request, 'account/pw-reset/sent.html')

    return render(request, 'account/pw-reset/send.html')


# /password/reset/<tokenid>
def password_reset(request, tokenid):
    token = ResetPWToken.objects.filter(tokenid=tokenid).first()
    if not token:
        return render(request, 'account/pw-reset/fail.html')

    if token.expire_time < timezone.now():
        token.delete()
        logger.warning('pw.reset.fail: expired token, username=%s' % token.user.username, request)
        return render(request, 'account/pw-reset/fail.html')

    if request.method == 'POST':
        user = token.user
        new_pw = request.POST.get('password', 'P@55w0rd!#$')
        user.set_password(new_pw)
        user.save()
        token.delete()

        logger.warning('pw.reset.success: username=%s' % user.username, request)
        return render(request, 'account/pw-reset/success.html')

    return render(request, 'account/pw-reset/main.html', {'tokenid': tokenid})


# /signup/, /signup/social/
def signup(request, is_social=False):
    if request.user.is_authenticated():
        return redirect('/')

    if is_social and 'info_signup' not in request.session:
        return redirect('/')

    signup = request.session.get('info_signup', {'type': 'EMAIL', 'profile': {'gender': 'E'}})
    type = signup['type']
    info = signup['profile']

    if request.method == 'POST':
        user = signup_backend(request.POST)

        if user is None:
            logger.warning('signup.fail')
            raise SuspiciousOperation()

        if type == 'FB':
            user.profile.facebook_id = info['userid']
        elif type == 'TW':
            user.profile.twitter_id = info['userid']
        elif type == 'KAIST':
            user.profile.kaist_id = info['userid']
            user.profile.kaist_info = info['kaist_info']

        user.profile.save()
        request.session.pop('info_signup', None)
        logger.warning('signup.success: username=%s, type=%s' % (user.username, type), request)
        return render(request, 'account/signup/complete.html', {'type': type})

    return render(request, 'account/signup/main.html', {'type': type, 'info': info})


# /callback/
def auth_callback(request):
    auth = request.session.pop('info_auth', None)
    if not auth:
        return redirect('/')

    mode, type = auth['mode'], auth['type']
    user, profile = None, None

    if type == 'FB':
        code = request.GET.get('code')
        user, profile = authenticate_fb(request, code)
    elif type == 'TW':
        user, profile = authenticate_tw(request)
    elif type == 'KAIST':
        token = request.COOKIES.get('SATHTOKEN')
        user, profile = authenticate_kaist(request, token)
    else:
        raise SuspiciousOperation()

    if mode == 'LOGIN':
        return login_callback(request, type, user, profile)
    elif mode == 'CONN':
        return connection_callback(request, type, user, profile)
    raise SuspiciousOperation()


# from /callback/
def login_callback(request, type, user, profile):
    if user:
        request.session.pop('info_user', None)
        request.session.pop('info_signup', None)

        user.backend = 'django.contrib.auth.backends.ModelBackend'
        auth.login(request, user)
        logger.info('login.success', request)

        if user.profile.expire_time:
            user.profile.expire_time = None
            user.profile.save()
            logger.warning('activate', request)

        nexturl = request.session.pop('next', '/')
        return redirect(nexturl)

    request.session['info_signup'] = {'type': type, 'profile': profile}

    response = redirect('/account/signup/')
    response.delete_cookie('SATHTOKEN')
    return response

# from /callback/
def connection_callback(request, type, user, ext_profile):
    if user:
        request.session['result_con'] = 1
        logger.warning('profile.connect.fail: type=%s' % type, request)
        return redirect('/account/profile/')

    profile = request.user.profile
    if type == 'FB' and not profile.facebook_id:
        profile.facebook_id = ext_profile['userid']
    elif type == 'TW' and not profile.twitter_id:
        profile.twitter_id = ext_profile['userid']
    elif type == 'KAIST' and not profile.kaist_id:
        profile.kaist_id = ext_profile['userid']
        profile.kaist_info = ext_profile['kaist_info']
    else:
        raise SuspiciousOperation()

    profile.save()

    logger.warning('profile.connect.success: type=%s' % type, request)
    request.session['result_con'] = 0

    response = redirect('/account/profile/')
    response.delete_cookie('SATHTOKEN')
    return response



# /util/email/check/
def email_check(request):
    if validate_email(request.GET.get('email', '')):
        return HttpResponse(status=200)
    return HttpResponse(status=400)

