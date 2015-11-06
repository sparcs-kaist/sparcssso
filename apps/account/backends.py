# -* coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from apps.account.forms import UserForm, UserProfileForm
from apps.account.models import UserProfile, EmailAuthToken, ResetPWToken
import cgi
import datetime
import json
import oauth2 as oauth
import os
import re
import urllib

# {male, female, etc} -> {M, F, E}
def parse_gender(gender):
    if gender == 'male':
        return 'M'
    elif gender == 'female':
        return 'F'
    return 'E'


# make username without duplication
def make_username():
    while True:
        username = os.urandom(10).encode('hex')
        if len(User.objects.filter(username=username)) == 0:
            return username


# make email auth token without duplication
def make_email_auth_tokenid():
    while True:
        tokenid = os.urandom(24).encode('hex')
        if len(EmailAuthToken.objects.filter(tokenid=tokenid)) == 0:
            return tokenid


# make reset password token without duplication
def make_reset_pw_tokenid():
    while True:
        tokenid = os.urandom(24).encode('hex')
        if len(ResetPWToken.objects.filter(tokenid=tokenid)) == 0:
            return tokenid


# give email auth token to user
def give_email_auth_token(user):
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

    for old_token in EmailAuthToken.objects.filter(user=user):
        old_token.delete()

    tokenid = make_email_auth_tokenid()
    token = EmailAuthToken(tokenid=tokenid, expire_time=tomorrow)
    token.user = user

    send_mail('[SPARCS SSO] E-mail Authorization',
              'To get auth, please enter http://sso.sparcs.org' +
              '/account/auth/email/'+tokenid+' until tomorrow this time.',
              'noreply@sso.sparcs.org', [user.email])

    token.save()


# give reset pw token to user
def give_reset_pw_token(user):
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

    for old_token in ResetPWToken.objects.filter(user=user):
        old_token.delete()

    tokenid = make_reset_pw_tokenid()
    token = ResetPWToken(tokenid=tokenid, expire_time=tomorrow)
    token.user = user

    send_mail('[SPARCS SSO] Reset Your Password',
              'To reset your password, please enter http://sso.sparcs.org' +
              '/account/password/reset/'+tokenid+' until tomorrow' +
              'this time.', 'noreply@sso.sparcs.org', [user.email])

    token.save()


# get username using email
def get_username(email):
    user = User.objects.filter(email=email)
    if len(user) > 0:
        return user[0].username
    return None


# check given email is available or not
def validate_email(email):
    if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return False

    users = User.objects.filter(email=email)
    if len(users) > 0:
        return False
    return True


# signup backend
def signup_backend(post):
    user_f = UserForm(post)
    profile_f = UserProfileForm(post)
    raw_email = post.get('email', '')

    if validate_email(raw_email) and user_f.is_valid() and profile_f.is_valid():
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

        profile = profile_f.save(commit=False)
        profile.user = user
        profile.save()

        give_email_auth_token(user)

        return user
    else:
        return None


# Facebook auth
def authenticate_fb(request, code):
    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'client_secret': settings.FACEBOOK_APP_SECRET,
        'redirect_uri': request.build_absolute_uri('/account/callback/'),
        'code': code,
    }

    target = urllib.urlopen('https://graph.facebook.com/oauth/access_token?' +
                            urllib.urlencode(args)).read()
    response = cgi.parse_qs(target)
    access_token = response['access_token'][-1]

    fb_info = urllib.urlopen('https://graph.facebook.com/v2.5/me?fields=email,first_name,last_name,gender,birthday&access_token=%s'
                                % access_token)
    fb_info = json.load(fb_info)

    profile = {'userid': fb_info['id'],
               'email': fb_info.get('email'),
               'first_name': fb_info.get('first_name'),
               'last_name': fb_info.get('last_name'),
               'gender': parse_gender(fb_info.get('gender')),
               'birthday': fb_info.get('birthday')}

    profiles = UserProfile.objects.filter(facebook_id=profile['userid'])
    if len(profiles) == 1:
        return profiles[0].user, None
    elif len(profiles) == 0:
        return None, profile
    return None, None


# Twitter OAuth Params
tw_consumer = oauth.Consumer(settings.TWITTER_APP_ID, settings.TWITTER_APP_SECRET)
tw_client = oauth.Client(tw_consumer)
tw_request_url = 'https://twitter.com/oauth/request_token'
tw_access_url = 'https://twitter.com/oauth/access_token'
tw_auth_url = 'https://twitter.com/oauth/authenticate'


# Twitter auth
def authenticate_tw(request):
    token = oauth.Token(request.session['request_token']['oauth_token'],
                        request.session['request_token']['oauth_token_secret'])
    token.set_verifier(request.GET['oauth_verifier'])
    client = oauth.Client(tw_consumer, token)

    resp, content = client.request(tw_access_url, 'POST')
    tw_info = dict(cgi.parse_qsl(content))

    profile = {'userid': tw_info['user_id'],
               'first_name': tw_info['screen_name'],
               'gender': 'E'}

    profiles = UserProfile.objects.filter(twitter_id=profile['userid'])
    if len(profiles) == 1:
        return profiles[0].user, None
    elif len(profiles) == 0:
        return None, profile
    return None, None


# KAIST auth
def authenticate_kaist(request):
    # TODO
    return None, None

