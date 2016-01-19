# -* coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from apps.account.forms import UserForm, UserProfileForm
from apps.account.models import UserProfile
from xml.etree.ElementTree import fromstring
import cgi
import httplib
import json
import logging
import oauth2 as oauth
import os
import re
import urllib


logger = logging.getLogger('sso.account.backend')


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


# Facebook
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

    target = urllib.urlopen('https://graph.facebook.com/oauth/access_token?' +
                            urllib.urlencode(args)).read()
    response = cgi.parse_qs(target)
    access_token = response['access_token'][-1]

    fb_info = urllib.urlopen('https://graph.facebook.com/v2.5/me?fields=' +
                             'email,first_name,last_name,gender,birthday&' +
                             'access_token=%s' % access_token)
    fb_info = json.load(fb_info)

    info = {'userid': fb_info['id'],
            'email': fb_info.get('email'),
            'first_name': fb_info.get('first_name'),
            'last_name': fb_info.get('last_name'),
            'gender': parse_gender(fb_info.get('gender')),
            'birthday': fb_info.get('birthday')}


    return UserProfile.objects.filter(facebook_id=info['userid']).first(), info


# Twitter
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
            'gender': 'E'}

    return UserProfile.objects.filter(twitter_id=info['userid']).first(), info


# KAIST
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
    encdata = data.encode('utf-8')

    conn = httplib.HTTPSConnection('iam.kaist.ac.kr')
    headers = {'Content-Type': 'text/xml', 'Content-Length': str(len(encdata))}

    conn.request('POST', '/iamps/services/singlauth/', '', headers)
    conn.send(encdata)

    raw_info = fromstring(conn.getresponse().read())[0][0][0]
    k_info = {}
    for node in raw_info:
        k_info[node.tag] = node.text

    info = {'userid': k_info['kaist_uid'],
            'email': k_info.get('mail'),
            'first_name': k_info.get('givenname'),
            'last_name': k_info.get('sn'),
            'gender': k_info.get('ku_sex'),
            'birthday': k_info.get('ku_born_date').replace('/', '-'),
            'kaist_info': k_info}

    return UserProfile.objects.filter(kaist_id=info['userid']).first(), info

