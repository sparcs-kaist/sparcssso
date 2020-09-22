import logging
import re
from urllib.parse import parse_qsl, urlencode
from xml.etree import ElementTree

import json
import ldap3
import oauth2 as oauth
import requests
import uuid
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

from apps.core.backends.util import parse_gender
from apps.core.models import UserProfile


logger = logging.getLogger('sso.auth')


# log any inactive user access
def check_active_user(request, user):
    if user and not user.is_active:
        logger.warning('login.reject', {
            'r': request,
            'uid': user.username,
            'hide': True,
        })
    return user.is_active if user else True


# login backends that uses email and password
class EmailLoginBackend(ModelBackend):
    def authenticate(self, request=None, email=None, password=None):
        user = User.objects.filter(email=email).first()
        if not check_active_user(request, user):
            return

        username = user.username if user else f'unknown:{email}'
        return super().authenticate(
            request=request, username=username, password=password,
        )


# login backends that uses LDAP id and password
class LDAPLoginBackend(ModelBackend):
    def authenticate(self, request=None, ldap_id=None, ldap_pw=None):
        user = User.objects.filter(profile__sparcs_id=ldap_id).first()
        if not check_active_user(request, user):
            return

        # prevent LDAP injection attack
        # the regex is taken from NAME_REGEX in adduser
        if not re.match(r'^[a-z][-a-z0-9]*$', ldap_id):
            return

        ldap_server = ldap3.Server(
            'ldap://sparcs.org', use_ssl=True, get_info=ldap3.ALL,
        )
        ldap_connection = ldap3.Connection(
            ldap_server,
            user=f'uid={ldap_id},ou=People,dc=sparcs,dc=org',
            password=ldap_pw,
        )
        if not ldap_connection.bind():
            return
        return user


# login backends that uses user object itself
class PasswordlessLoginBackend(ModelBackend):
    def authenticate(self, request=None, user=None):
        if not check_active_user(request, user):
            return

        # deny password-less staff login
        if user and user.is_staff:
            logger.error('login.error', {
                'r': request,
                'uid': user.username,
            })
            return None
        return user


# Facebook Init & Auth
def auth_fb_init(callback_url):
    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'auth_type': 'rerequest',
        'scope': 'email',
        'redirect_uri': callback_url,
    }
    return f'https://www.facebook.com/dialog/oauth?{urlencode(args)}'


def auth_fb_callback(code, callback_url):
    # get access token
    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'client_secret': settings.FACEBOOK_APP_SECRET,
        'redirect_uri': callback_url,
        'code': code,
    }
    token_info = requests.get(
        'https://graph.facebook.com/oauth/access_token?',
        params=args, verify=True).json()
    if 'access_token' not in token_info:
        return None, None

    # get grant info
    access_token = token_info['access_token']
    args = {
        'access_token': access_token,
    }
    grant_info = requests.get('https://graph.facebook.com/v2.5/me/permissions',
                              params=args, verify=True).json()
    for data in grant_info['data']:
        if data['status'] == 'declined':
            return None, None

    # get facebook profile
    args = {
        'fields': 'email,first_name,last_name,gender,birthday',
        'access_token': access_token,
    }
    fb_info = requests.get('https://graph.facebook.com/v2.5/me',
                           params=args, verify=True).json()
    info = {
        'userid': fb_info['id'],
        'email': fb_info.get('email'),
        'first_name': fb_info.get('first_name'),
        'last_name': fb_info.get('last_name'),
        'gender': parse_gender(fb_info.get('gender')),
        'birthday': fb_info.get('birthday'),
    }
    fb_profile = UserProfile.objects.filter(facebook_id=info['userid'],
                                            test_only=False).first()
    return fb_profile, info


# Twitter Init & Auth
tw_consumer = oauth.Consumer(settings.TWITTER_APP_ID,
                             settings.TWITTER_APP_SECRET)
tw_client = oauth.Client(tw_consumer)


def auth_tw_init(callback_url):
    body = f'oauth_callback={callback_url}'
    resp, content = tw_client.request(
        'https://twitter.com/oauth/request_token', 'POST', body)

    tokens = dict(parse_qsl(content.decode('utf-8')))
    oauth_token = tokens['oauth_token']
    url = f'https://twitter.com/oauth/authenticate?oauth_token={oauth_token}'
    return url, tokens


def auth_tw_callback(tokens, verifier):
    token = oauth.Token(tokens['oauth_token'], tokens['oauth_token_secret'])
    token.set_verifier(verifier)
    client = oauth.Client(tw_consumer, token)

    resp, content = client.request(
        'https://twitter.com/oauth/access_token', 'POST')
    tw_info = dict(parse_qsl(content.decode('utf-8')))

    # access denied
    if 'user_id' not in tw_info:
        return None, None

    info = {
        'userid': tw_info['user_id'],
        'first_name': tw_info['screen_name'],
        'gender': '*H',
    }
    tw_profile = UserProfile.objects.filter(twitter_id=info['userid'],
                                            test_only=False).first()
    return tw_profile, info


# KAIST Auth
def auth_kaist_init(callback_url):
    state = str(uuid.uuid4())
    args = {
        'client_id': 'SPARCS',
        'state': state,
        'redirect_url': callback_url
    }
    
    return f'https://iam2.kaist.ac.kr/api/sso/commonLogin?{urlencode(args)}', state


def auth_kaist_callback(token, iam_info_raw):
    iam_info = json.loads(iam_info_raw)['dataMap']
    state = iam_info['state']

    if state != token:
        return None, None, False

    k_info = iam_info['USER_INFO']

    info = {
        'userid': k_info['kaist_uid'],
        'email': k_info.get('mail'),
        'first_name': k_info.get('givenname'),
        'last_name': k_info.get('sn'),
        'gender': f'*{k_info.get("ku_sex")}',
        'birthday': k_info.get('ku_born_date').replace('/', '-'),
        'kaist_info': k_info,
    }
    kaist_profile = UserProfile.objects.filter(kaist_id=info['userid'],
                                               test_only=False).first()
    return kaist_profile, info, True
