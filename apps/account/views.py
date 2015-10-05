# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from apps.account.models import UserProfile, SocialSignupInfo,\
    EmailAuthToken, ResetPWToken
from apps.account.forms import UserForm, UserProfileForm
from apps.oauth.models import Service
from urlparse import urlparse, parse_qs
import cgi
import json
import os
import oauth2 as oauth
import re
import urllib
import datetime


# Helper functions
def parse_gender(gender):
    if gender == 'male':
        return 'M'
    elif gender == 'female':
        return 'F'
    else:
        return 'E'


def make_username():
    while True:
        username = os.urandom(10).encode('hex')
        if len(User.objects.filter(username=username)) == 0:
            return username


def make_auth_token():
    while True:
        token = os.urandom(24).encode('hex')
        if len(EmailAuthToken.objects.filter(token=token)) == 0:
            return token


def make_resetpw_token():
    while True:
        token = os.urandom(24).encode('hex')
        if len(ResetPWToken.objects.filter(token=token)) == 0:
            return token


def give_auth_token(user):
    user_profile = user.user_profile
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

    for token_element in EmailAuthToken.objects\
            .filter(user_profile=user_profile):
        token_element.delete()

    token = make_auth_token()
    email_auth_token = EmailAuthToken(token=token,
                                      expire_time=tomorrow)
    email_auth_token.user_profile = user_profile

    send_mail('[SPARCS SSO] E-mail Authorization',
              'To get auth, please enter http://sso.sparcs.org' +
              '/account/email-auth/'+token+' until tomorrow this time.',
              'noreply@sso.sparcs.org', [user.email])

    email_auth_token.save()


def give_resetpw_token(user):
    user_profile = user.user_profile
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

    for token_element in ResetPWToken.objects\
            .filter(user_profile=user_profile):
        token_element.delete()

    token = make_resetpw_token()
    reset_pw_token = ResetPWToken(token=token,
                                  expire_time=tomorrow)
    reset_pw_token.user_profile = user_profile

    send_mail('[SPARCS SSO] Reset Your Password',
              'To reset your password, please enter http://sso.sparcs.org' +
              '/account/password/reset/'+token+' until tomorrow' +
              'this time.', 'noreply@sso.sparcs.org', [user.email])

    reset_pw_token.save()


def get_username(email):
    user = User.objects.filter(email=email)
    if len(user) > 0:
        return user[0].username
    return ''


def validate_email(email):
    if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return False

    users = User.objects.filter(email=email)
    if len(users) > 0:
        return False
    return True


def authenticate_fb(request, mode, token):
    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'client_secret': settings.FACEBOOK_APP_SECRET,
        'redirect_uri': request.build_absolute_uri(
            '/account/' + mode + '/fb/callback/'),
        'code': token,
    }

    target = urllib.urlopen('https://graph.facebook.com/oauth/access_token?' +
                            urllib.urlencode(args)).read()
    response = cgi.parse_qs(target)
    access_token = response['access_token'][-1]

    fb_profile = urllib.urlopen('https://graph.facebook.com/me?access_token=%s'
                                % access_token)
    fb_profile = json.load(fb_profile)

    user_profiles = UserProfile.objects.filter(facebook_id=fb_profile['id'])

    if len(user_profiles) == 1:
        return {'user': user_profiles[0].user, 'fb_profile': fb_profile}
    elif len(user_profiles) == 0:
        return {'user': None, 'fb_profile': fb_profile}
    raise SuspiciousOperation('Multiple users')


# Twitter OAuth
tw_consumer = oauth.Consumer(settings.TWITTER_APP_ID,
                             settings.TWITTER_APP_SECRET)
tw_client = oauth.Client(tw_consumer)
tw_request_url = 'https://twitter.com/oauth/request_token'
tw_access_url = 'https://twitter.com/oauth/access_token'
tw_auth_url = 'https://twitter.com/oauth/authenticate'


def authenticate_tw(request):
    token = oauth.Token(request.session['request_token']['oauth_token'],
                        request.session['request_token']['oauth_token_secret'])
    token.set_verifier(request.GET['oauth_verifier'])
    client = oauth.Client(tw_consumer, token)

    resp, content = client.request(tw_access_url, 'POST')
    tw_profile = dict(cgi.parse_qsl(content))

    user_profiles = UserProfile.objects\
        .filter(twitter_id=tw_profile['user_id'])

    if len(user_profiles) == 1:
        return {'user': user_profiles[0].user, 'tw_profile': tw_profile}
    elif len(user_profiles) == 0:
        return {'user': None, 'tw_profile': tw_profile}
    raise SuspiciousOperation('Multiple users')


def signup_backend(post):
    user_f = UserForm(post)
    user_profile_f = UserProfileForm(post)
    raw_email = post.get('email', '')

    if validate_email(raw_email) and user_f.is_valid() \
            and user_profile_f.is_valid():
        email = user_f.cleaned_data['email']
        password = user_f.cleaned_data['password']
        first_name = user_f.cleaned_data['first_name']
        last_name = user_f.cleaned_data['last_name']
        username = make_username()
        user = User.objects.create_user(username=username,
                                        first_name=first_name,
                                        last_name=last_name,
                                        email=email, password=password)

        user.save()

        user_profile = user_profile_f.save(commit=False)
        user_profile.user = user
        user_profile.save()

        give_auth_token(user)

        return user
    else:
        return None


# Main Page
def main(request):
    return render(request, 'main.html')


# Credit Page
def credit(request):
    return render(request, 'credit.html')


# Email Login
def login_email(request):
    if request.user.is_authenticated():
        return redirect('/')

    if request.method == 'POST':
        email = request.POST.get('email', 'none')
        password = request.POST.get('password', 'asdf')
        nexturl = request.POST.get('next', '/')

        username = get_username(email)
        user = auth.authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return render(request, 'account/login.html',
                          {'next': nexturl, 'msg': 'Invalid Account Info'})
        elif not user.user_profile.email_authed:
            return render(request, 'account/reauth.html',
                          {'username': username})
        else:
            auth.login(request, user)

            if 'next' in request.session:
                nexturl = request.session.pop('next')
            return redirect(nexturl)

    if 'next' in request.GET:
        url = request.GET['next']
        if url.startswith('/oauth/require/'):
            request.session['next'] = url

    return render(request, 'account/login.html',
                  {'next': request.GET.get('next', '/')})


# Facebook Login & Connect Init
def fb_auth_init(request, mode):
    is_authed = request.user.is_authenticated()
    if (mode == 'login' and is_authed) or \
       (mode == 'connect' and not is_authed):
        return redirect('/')

    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'scope': 'email',
        'redirect_uri': request.build_absolute_uri(
            '/account/' + mode + '/fb/callback/'),
    }
    return redirect('https://www.facebook.com/dialog/oauth?' +
                    urllib.urlencode(args))


# Facebook Login Callback
def login_fb_callback(request):
    if request.user.is_authenticated():
        return redirect('/')

    code = request.GET.get('code')
    data = authenticate_fb(request, 'login', code)

    if data['user'] is None:
        profile = data['fb_profile']
        signup_info = SocialSignupInfo.objects.filter(
            userid=profile['id']).filter(type='FB').first()

        if signup_info is None:
            signup_info = SocialSignupInfo(userid=profile['id'],
                                           type='FB', email=profile['email'],
                                           first_name=profile['first_name'],
                                           last_name=profile['last_name'],
                                           gender=parse_gender(
                                               profile['gender']))
            signup_info.save()
        return redirect('/account/signup/fb/' + signup_info.userid)
    else:
        data['user'].backend = 'django.contrib.auth.backends.ModelBackend'
        auth.login(request, data['user'])

        nexturl = request.session.pop('next', '/')
        return redirect(nexturl)


# Facebook Connect
@login_required
def connect_fb_callback(request):
    code = request.GET.get('code')
    data = authenticate_fb(request, 'connect', code)

    profile = request.user.user_profile
    if profile.facebook_id != '':
        return redirect('/account/profile/?con=1')

    users = UserProfile.objects.filter(facebook_id=data['fb_profile']['id'])
    if len(users) > 0:
        return redirect('/account/profile/?con=2')

    userid = data['fb_profile']['id']
    profile.facebook_id = userid
    profile.save()

    signup_info = SocialSignupInfo.objects.filter(userid=userid).\
        filter(type='FB').first()
    if signup_info is not None:
        signup_info.delete()

    return redirect('/account/profile/?con=0')


# Twitter Login & Connect Init
def tw_auth_init(request, mode):
    is_authed = request.user.is_authenticated()
    if (mode == 'login' and is_authed) or \
       (mode == 'connect' and not is_authed):
        return redirect('/')

    body = 'oauth_callback=' + request.build_absolute_uri(
        '/account/' + mode + '/tw/callback/')
    resp, content = tw_client.request(tw_request_url, 'POST', body)

    request.session['request_token'] = dict(cgi.parse_qsl(content))
    url = '%s?oauth_token=%s' % (tw_auth_url, request.session
                                 ['request_token']['oauth_token'])

    return redirect(url)


# Twitter Login Callback
def login_tw_callback(request):
    if request.user.is_authenticated():
        return redirect('/')

    data = authenticate_tw(request)

    if data['user'] is None:
        profile = data['tw_profile']
        signup_info = SocialSignupInfo.objects.filter(
            userid=profile['user_id']).filter(type='TW').first()

        if signup_info is None:
            signup_info = SocialSignupInfo(userid=profile['user_id'],
                                           type='TW', email='',
                                           first_name=profile['screen_name'],
                                           last_name='', gender='E')
            signup_info.save()
        return redirect('/account/signup/tw/' + signup_info.userid)
    else:
        data['user'].backend = 'django.contrib.auth.backends.ModelBackend'
        auth.login(request, data['user'])

        nexturl = request.session.pop('next', '/')
        return redirect(nexturl)


# Twitter Connect
@login_required
def connect_tw_callback(request):
    data = authenticate_tw(request)

    profile = request.user.user_profile
    if profile.twitter_id != '':
        return redirect('/account/profile/?con=1')

    users = UserProfile.objects\
        .filter(twitter_id=data['tw_profile']['user_id'])
    if len(users) > 0:
        return redirect('/account/profile/?con=2')

    userid = data['tw_profile']['user_id']
    profile.twitter_id = userid
    profile.save()

    signup_info = SocialSignupInfo.objects.filter(userid=userid).\
        filter(type='TW').first()
    if signup_info is not None:
        signup_info.delete()

    return redirect('/account/profile/?con=0')


# Logout
def logout(request):
    if not request.user.is_authenticated():
        return redirect('/')

    auth.logout(request)
    return render(request, 'account/logout.html')


# Signup with Email
def signup(request):
    if request.user.is_authenticated():
        return redirect('/')

    if request.method == 'POST':
        user = signup_backend(request.POST)

        if user is None:
            raise SuspiciousOperation("Not valid POST data")
        return redirect('/')

    return render(request, 'account/signup.html')


# Signup with Social Account
def signup_social(request, userid, type):
    if request.user.is_authenticated():
        return redirect('/')

    signup_info = SocialSignupInfo.objects.filter(userid=userid).\
        filter(type=type).first()

    if signup_info is None:
        raise Http404()

    if request.method == 'POST':
        user = signup_backend(request.POST)

        if user is None:
            raise SuspiciousOperation("Not valid POST data")

        if type == 'FB':
            user.user_profile.facebook_id = signup_info.userid
        elif type == 'TW':
            user.user_profile.twitter_id = signup_info.userid
        elif type == 'KAIST':
            user.user_profile.kaist_id = signup_info.userid
        user.user_profile.save()

        signup_info.delete()
        return redirect('/')

    return render(request, 'account/signup_social.html', {'info': signup_info})


# Disconnect Social Account
@login_required
def disconnect(request, type):
    if request.method != 'POST':
        return SuspiciousOperation('Only post permitted')

    profile = request.user.user_profile
    if type == 'FB':
        profile.facebook_id = ''
    elif type == 'TW':
        profile.twitter_id = ''
    elif type == 'KAIST':
        profile.kaist_id = ''
    profile.save()

    return redirect('/account/profile/?con=5')


# Email Duplication Check
def email_check(request):
    if validate_email(request.GET.get('email', '')):
        return HttpResponse(status=200)
    return HttpResponse(status=400)


# Email Auth
def email_auth(request, token):
    for token_element in EmailAuthToken.objects.filter(token=token):
        if token_element.expire_time.replace(tzinfo=None) >\
           datetime.datetime.now().replace(tzinfo=None):
            token_element.user_profile.email_authed = True
            token_element.user_profile.save()
            token_element.delete()
            return render(request, 'account/email-auth/success.html')
    return render(request, 'account/email-auth/fail.html')


# Send Account Auth Email
def send_auth_email(request):
    if request.method == 'POST':
        nexturl = request.POST.get('next', '/')
        username = request.POST.get('username', 'none')
    else:
        return render(request, 'account/login.html')
    user = User.objects.get(username=username)
    give_auth_token(user)
    user.user_profile.save()
    return render(request, 'account/login.html',
                  {'next': nexturl, 'msg': 'Auth E-mail was sent. \
                                            Please check your e-mail.'})


# Send Password Reset Email
def send_reset_email(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        if (email != ''):
            if len(User.objects.filter(email=email)) != 0:
                user = User.objects.get(email=email)
                give_resetpw_token(user)
                user.user_profile.save()
                return render(request, 'account/reset-pw/sent.html')
            else:
                return render(request, 'account/reset-pw/check.html',
                              {'msg': 'Cannot find user with such e-mail.'})
    return render(request, 'account/reset-pw/check.html')


# View Profile
@login_required
def profile(request):
    user = request.user
    userprofile = UserProfile.objects.get(user=user)

    msg = ''
    conn_msg = ''
    conn_msg_mode = 'success'
    if request.method == "POST":
        user_f = UserForm(request.POST)
        user_profile_f = UserProfileForm(request.POST, instance=userprofile)

        if user_f.is_valid() and user_profile_f.is_valid():
            user.first_name = user_f.cleaned_data['first_name']
            user.last_name = user_f.cleaned_data['last_name']
            user.save()

            userprofile = user_profile_f.save()
            msg = 'Your profile was successfully modified!'
    elif request.method == "GET":
        con = request.GET.get('con', '')
        if con == '0':
            conn_msg = '성공적으로 연동되었습니다!!'
        elif con == '5':
            conn_msg = '연동 해제되었습니다.'
        elif con == '1':
            conn_msg = '이미 해당 Social 계정을 연동하셨습니다.'
            conn_msg_mode = 'danger'
        elif con == '2':
            conn_msg = '다른 사람이 연동한 계정입니다.'
            conn_msg_mode = 'danger'

    return render(request, 'account/profile.html',
                  {'user': user, 'userprofile': userprofile, 'msg': msg,
                   'conn_msg': conn_msg, 'conn_msg_mode': conn_msg_mode})


# Password Change
@login_required
def password_change(request):
    user = request.user

    msg = ''
    if request.method == "POST":
        oldpw = request.POST.get('oldpassword', '')
        newpw = request.POST.get('password', 'P@55w0rd!#$')

        if check_password(oldpw, user.password):
            user.password = make_password(newpw)
            user.save()
            return redirect('/account/login')
        else:
            msg = 'Wrong current password.'

    return render(request, 'account/changepw.html', {'user': user, 'msg': msg})


# Password Reset
def password_reset(request, token):
    for token_element in ResetPWToken.objects.filter(token=token):
        if token_element.expire_time.replace(tzinfo=None) >\
           datetime.datetime.now().replace(tzinfo=None):
            if request.method == 'POST':
                new_pw = request.POST.get('password', '')
                if (new_pw != ''):
                    user = token_element.user_profile.user
                    user.set_password(new_pw)
                    user.save()
                    token_element.delete()
                    return render(request, 'account/reset-pw/success.html')
            else:
                return render(request, 'account/reset-pw/reset.html',
                              {'token': token})
    return render(request, 'account/reset-pw/fail.html')
