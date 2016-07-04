# -* coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from apps.core.models import ServiceMap, UserProfile, EmailAuthToken, ResetPWToken
from apps.core.forms import UserForm, UserProfileForm
from xml.etree.ElementTree import fromstring
import cgi
import datetime
import requests
import logging
import oauth2 as oauth
import os
import re
import urllib
import urlparse


logger = logging.getLogger('sso.account.backend')


# {male, female, etc} -> {M, F, E}
def parse_gender(gender):
    if gender == 'male':
        return '*M'
    elif gender == 'female':
        return '*F'
    return gender


# get username using email
def get_username(email):
    user = User.objects.filter(email=email).first()
    if user:
        return user.username
    return 'unknown'


# check given email is available or not
def validate_email(email):
    if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return False

    return User.objects.filter(email=email).count() == 0


# give reset pw token to user
def give_reset_pw_token(user):
    title = '[SPARCS SSO] Reset Password'
    message = 'To reset your password, please click <a href="https://sparcssso.kaist.ac.kr/account/password/reset/%s">this link</a> in 24 hours.'

    tomorrow = timezone.now() + datetime.timedelta(days=1)

    for token in ResetPWToken.objects.filter(user=user):
        token.delete()

    while True:
        tokenid = os.urandom(24).encode('hex')
        if not ResetPWToken.objects.filter(tokenid=tokenid).count():
            break

    token = ResetPWToken(tokenid=tokenid, expire_time=tomorrow, user=user).save()
    send_mail(title, '', 'noreply@sso.sparcs.org', [user.email],
              html_message=message % tokenid)


# give email auth token to user
def give_email_auth_token(user):
    title = '[SPARCS SSO] Email Authentication'
    message = 'To authenticate your email, <a href="https://sparcssso.kaist.ac.kr/account/auth/email/%s">this link</a> in 24 hours.'

    tomorrow = timezone.now() + datetime.timedelta(days=1)

    for token in EmailAuthToken.objects.filter(user=user):
        token.delete()

    while True:
        tokenid = os.urandom(24).encode('hex')
        if not EmailAuthToken.objects.filter(tokenid=tokenid).count():
            break

    token = EmailAuthToken(tokenid=tokenid, expire_time=tomorrow, user=user).save()
    send_mail(title, '', 'noreply@sso.sparcs.org', [user.email],
              html_message=message % tokenid)


# signup core
def signup_core(post):
    user_f = UserForm(post)
    profile_f = UserProfileForm(post)
    raw_email = post.get('email', '')

    if validate_email(raw_email) and user_f.is_valid() and profile_f.is_valid():
        email = user_f.cleaned_data['email']
        password = user_f.cleaned_data['password']
        first_name = user_f.cleaned_data['first_name']
        last_name = user_f.cleaned_data['last_name']
        while True:
            username = os.urandom(10).encode('hex')
            if not User.objects.filter(username=username).count():
                break

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


# Register Service
def reg_service(user, service):
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if m and not m.unregister_time:
        return False
    elif m and m.unregister_time and \
            (timezone.now() - m.unregister_time).days < service.cooltime:
        return False

    if m:
        m.delete()
    m = ServiceMap(user=user, service=service)

    while True:
        sid = os.urandom(10).encode('hex')
        if not ServiceMap.objects.filter(sid=sid).count():
            break

    m.sid = sid
    m.register_time = timezone.now()
    m.unregister_time = None
    m.save()

    return True


# Unregister Service
def unreg_service(user, service):
    default_result = {'status': '1', 'msg': 'Unknown Error'}
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if not m or m.unregister_time:
        return default_result

    r = requests.post(service.unregister_url, verify=True,
                      data={'sid': m.sid, 'key': service.secret_key})
    try:
        result = r.json()
        status = result.get('status', '1')
        if status != '0':
            return result
    except:
        return default_result

    m.unregister_time = timezone.now()
    m.save()
    return result


# Facebook Init & Auth
def init_fb(callback_url):
    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'scope': 'email',
        'redirect_uri': callback_url,
    }
    return 'https://www.facebook.com/dialog/oauth?' + urllib.urlencode(args)


def auth_fb(code, callback_url):
    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'client_secret': settings.FACEBOOK_APP_SECRET,
        'redirect_uri': callback_url,
        'code': code,
    }

    r = requests.get('https://graph.facebook.com/oauth/access_token?',
                     params=args, verify=True)
    response = urlparse.parse_qs(r.text)
    access_token = response['access_token'][-1]

    args = {
        'fields': 'email,first_name,last_name,gender,birthday',
        'access_token': access_token
    }
    r = requests.get('https://graph.facebook.com/v2.5/me',
                     params=args, verify=True)
    fb_info = r.json()

    info = {'userid': fb_info['id'],
            'email': fb_info.get('email'),
            'first_name': fb_info.get('first_name'),
            'last_name': fb_info.get('last_name'),
            'gender': parse_gender(fb_info.get('gender')),
            'birthday': fb_info.get('birthday')}

    return UserProfile.objects.filter(facebook_id=info['userid']).first(), info


# Twitter Init & Auth
tw_consumer = oauth.Consumer(settings.TWITTER_APP_ID, settings.TWITTER_APP_SECRET)
tw_client = oauth.Client(tw_consumer)


def init_tw(callback_url):
    body = 'oauth_callback=' + callback_url
    resp, content = tw_client.request('https://twitter.com/oauth/request_token', 'POST', body)

    tokens = dict(cgi.parse_qsl(content))
    url = 'https://twitter.com/oauth/authenticate?oauth_token=%s' % tokens['oauth_token']
    return url, tokens


def auth_tw(tokens, verifier):
    token = oauth.Token(tokens['oauth_token'], tokens['oauth_token_secret'])
    token.set_verifier(verifier)
    client = oauth.Client(tw_consumer, token)

    resp, content = client.request('https://twitter.com/oauth/access_token', 'POST')
    tw_info = dict(cgi.parse_qsl(content))

    info = {'userid': tw_info['user_id'],
            'first_name': tw_info['screen_name'],
            'gender': '*H'}

    return UserProfile.objects.filter(twitter_id=info['userid']).first(), info


# KAIST Auth
def auth_kaist(token):
    data = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://server.com">
    <soapenv:Header/>
    <soapenv:Body>
        <ser:verification>
            <cookieValue>%s</cookieValue>
            <publicKeyStr>%s</publicKeyStr>
            <adminVO>
                <adminId>%s</adminId>
                <password>%s</password>
            </adminVO>
        </ser:verification>
    </soapenv:Body>
</soapenv:Envelope>""" % (token, settings.KAIST_APP_SECRET, settings.KAIST_APP_ADMIN_ID, settings.KAIST_APP_ADMIN_PW)

    r = requests.post('https://iam.kaist.ac.kr/iamps/services/singlauth/',
                      data=data, verify=True)
    raw_info = fromstring(r.text)[0][0][0]
    k_info = {}
    for node in raw_info:
        k_info[node.tag] = node.text

    info = {'userid': k_info['kaist_uid'],
            'email': k_info.get('mail'),
            'first_name': k_info.get('givenname'),
            'last_name': k_info.get('sn'),
            'gender': '*%s' % k_info.get('ku_sex'),
            'birthday': k_info.get('ku_born_date').replace('/', '-'),
            'kaist_info': k_info}

    return UserProfile.objects.filter(kaist_id=info['userid']).first(), info


# Validate reCAPTCHA
def validate_recaptcha(response):
    data = {'secret': settings.RECAPTCHA_SECRET, 'response': response}
    r = requests.post('https://www.google.com/recaptcha/api/siteverify', data = data)

    result = r.json()
    return result["success"]
