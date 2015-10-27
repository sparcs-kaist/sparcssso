# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from apps.account.backends import give_email_auth_token, give_reset_pw_token, \
        get_username, validate_email, signup_backend, authenticate_fb, \
        authenticate_tw, authenticate_kaist, tw_client, tw_request_url, tw_auth_url
from apps.account.models import EmailAuthToken, ResetPWToken, Notice
from apps.account.forms import UserForm, UserProfileForm
from apps.oauth.models import Service
import cgi
import urllib
import datetime


# /login/{fb,tw,kaist}/, /connect/{fb,tw,kaist}/
def auth_init(request, mode, type):
    is_authed = request.user.is_authenticated()
    if (mode == 'LOGIN' and is_authed) or \
       (mode == 'CONN' and not is_authed):
        return redirect('/')

    request.session['info_auth'] = {'mode': mode, 'type': type}

    url = ''
    if type == 'FB':
        args = {
            'client_id': settings.FACEBOOK_APP_ID,
            'scope': 'email',
            'redirect_uri': request.build_absolute_uri('/account/callback/fb/'),
        }
        url = 'https://www.facebook.com/dialog/oauth?' + urllib.urlencode(args)
    elif type == 'TW':
        body = 'oauth_callback=' + request.build_absolute_uri('/account/callback/tw/')
        resp, content = tw_client.request(tw_request_url, 'POST', body)

        request.session['request_token'] = dict(cgi.parse_qsl(content))
        url = '%s?oauth_token=%s' % (tw_auth_url, request.session
                                     ['request_token']['oauth_token'])
    elif type == 'KAIST':
        pass # TODO

    return redirect(url)


# /main/
def main(request):
    current_time = timezone.now()
    services = Service.objects.filter(is_public=True)
    notice = Notice.objects.filter(valid_from__lte=current_time)\
            .filter(valid_to__gt=current_time)
    if notice:
        notice = notice[0]

    return render(request, 'main.html', {'services': services, 'notice': notice})


# /credit
def credit(request):
    return render(request, 'credit.html')


# /login/
def login(request):
    if request.user.is_authenticated():
        return redirect('/')

    if request.method == 'POST':
        email = request.POST.get('email', 'none')
        password = request.POST.get('password', 'asdf')

        username = get_username(email)
        user = auth.authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return render(request, 'account/login.html', {'fail': True})
        elif not user.profile.email_authed:
            request.session['info_user'] = user
            return redirect('/auth/email/resend/')
        else:
            request.session.pop('info_user', None)
            request.session.pop('info_signup', None)
            auth.login(request, user)

    # TODO: redirection
    return render(request, 'account/login.html')


# /logout/
def logout(request):
    if not request.user.is_authenticated():
        return redirect('/')

    auth.logout(request)
    return render(request, 'account/logout.html')


# /auth/email/
def auth_email_resend(request):
    if request.method != 'POST':
        return render(request, 'account/reauth.html')

    user = request.session.pop('info_user', None)
    if user is None or user.profile.email_authed:
        return redirect('/')

    give_email_auth_token(user[0])
    return redirect('/account/login/')


# /auth/email/<tokenid>
def auth_email(request, tokenid):
    tokens = EmailAuthToken.objects.filter(tokenid=tokenid)
    if len(tokens) == 0:
        return render(request, 'account/email-auth/fail.html')

    token = tokens[0]
    if token.expire_time.replace(tzinfo=None) < \
        datetime.datetime.now().replace(tzinfo=None):
        token.delete()
        return render(request, 'account/email-auth/fail.html')

    token.user.profile.email_authed = True
    token.user.profile.save()
    token.delete()
    return render(request, 'account/email-auth/success.html')


# /profile/
@login_required
def profile(request):
    user = request.user
    profile = user.profile

    success = False
    result_con = request.session.pop('result_con', 0)
    if request.method == 'POST':
        user_f = UserForm(request.POST)
        profile_f = UserProfileForm(request.POST, instance=profile)

        if user_f.is_valid() and profile_f.is_valid():
            user.first_name = user_f.cleaned_data['first_name']
            user.last_name = user_f.cleaned_data['last_name']
            user.save()

            profile = profile_f.save()
            success = True

    return render(request, 'account/profile.html',
                  {'user': user, 'profile': profile,
                   'success': success, 'result_con': result_con})


# /disconnect/{fb,tw,kaist}/
@login_required
def disconnect(request, type):
    if request.method != 'POST':
        return SuspiciousOperation()

    profile = request.user.profile
    if type == 'FB':
        profile.facebook_id = ''
    elif type == 'TW':
        profile.twitter_id = ''
    elif type == 'KAIST':
        profile.kaist_id = ''
        profile.kaist_info = ''
    profile.save()

    request.session['result_con'] = 5
    return redirect('/account/profile/')


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
            return redirect('/account/login')
        else:
            fail = True

    return render(request, 'account/changepw.html', {'user': user, 'fail': fail})


# /password/reset/
def password_reset_email(request):
    if request.method != 'POST':
        return render(request, 'account/reset-pw/check.html')

    email = request.POST.get('email', '')
    users = User.objects.filter(email=email)
    if len(users) == 0:
        return render(request, 'account/reset-pw/check.html', {'fail': True})

    give_reset_pw_token(users[0])
    return render(request, 'account/reset-pw/sent.html')


# /password/reset/<tokenid>
def password_reset(request, tokenid):
    tokens = ResetPWToken.objects.filter(tokenid=tokenid)
    if len(tokens) == 0:
        return render(request, 'account/reset-pw/fail.html')

    token = tokens[0]
    if token.expire_time.replace(tzinfo=None) < \
        datetime.datetime.now().replace(tzinfo=None):
        token.delete()
        return render(request, 'account/reset-pw/fail.html')

    if request.method == 'POST':
        new_pw = request.POST.get('password', 'P@55w0rd!#$')
        user = token.user
        user.set_password(new_pw)
        user.save()
        token.delete()
        return render(request, 'account/reset-pw/success.html')

    return render(request, 'account/reset-pw/reset.html', {'tokenid': tokenid})


# /signup/, /signup/social/
def signup(request, is_social):
    if request.user.is_authenticated():
        return redirect('/')

    if is_social and 'info_signup' not in request.session:
        return redirect('/')

    signup = request.session.get('info_signup', {'type': 'email', 'profile': {}})
    type = signup['type']
    info = signup['profile']

    if request.method == 'POST':
        user = signup_backend(request.POST)

        if user is None:
            raise SuspiciousOperation()

        if type == 'FB':
            user.profile.facebook_id = info.userid
        elif type == 'TW':
            user.profile.twitter_id = info.userid
        elif type == 'KAIST':
            user.profile.kaist_id = info.userid
            user.profile.kaist_info = info.kaist_info

        user.profile.save()
        request.session.pop('info_signup', None)

        return redirect('/')

    return render(request, 'account/signup.html', {'type': type, 'profile': profile})


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
        user, profile = authenticate_kaist(request)
    else:
        raise SuspiciousOperation()

    if mode == 'LOGIN':
        request.session.pop('info_user', None)
        request.session.pop('info_signup', None)
        login_callback(request, user, profile)
    elif mode == 'CONN':
        connection_callback(request, type, user, profile)
    raise SuspiciousOperation()


# from /callback/
def login_callback(request, user, profile):
    if user:
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        auth.login(request, user)

        # TODO: redirection
        nexturl = request.session.pop('next', '/')
        return redirect(nexturl)

    request.session['info_signup'] = {'type': type, 'profile': profile}
    return redirect('/account/signup/')


# from /callback/
def connection_callback(request, type, user, ext_profile):
    if request.user != user:
        request.session['result_con'] = 2
        return redirect('/account/profile/')

    result_con = 1
    profile = user.profile
    if type == 'FB' and not profile.facebook_id:
        profile.facebook_id = ext_profile['userid']
        profile.save()
        result_con = 0
    elif type == 'TW' and not profile.twitter_id:
        profile.twitter_id = ext_profile['userid']
        profile.save()
        result_con = 0
    elif type == 'KAIST' and not profile.kaist_id:
        profile.kaist_id = ext_profile['userid']
        profile.kaist_info = ext_profile['kaist_info']
        result_con = 0
    else:
        raise SuspiciousOperation()

    request.session['result_con'] = result_con
    return redirect('/account/profile/')


# /util/email/check
def email_check(request):
    if validate_email(request.GET.get('email', '')):
        return HttpResponse(status=200)
    return HttpResponse(status=400)

