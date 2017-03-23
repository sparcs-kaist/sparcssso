from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from apps.core.models import ServiceMap, UserProfile, \
    EmailAuthToken, ResetPWToken
from apps.core.messages import ResetPWMessage, EmailAuthMessage
from apps.core.forms import UserForm
from secrets import token_hex
from xml.etree import ElementTree
from urllib.parse import parse_qs, parse_qsl, urlencode
import datetime
import requests
import logging
import oauth2 as oauth
import re


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
def validate_email(email, exclude=''):
    if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return False

    return User.objects.filter(email=email) \
        .exclude(email=exclude).count() == 0


# give reset pw token to user
def give_reset_pw_token(user):
    if user.email.endswith('@sso.sparcs.org'):
        return

    while True:
        tokenid = token_hex(24)
        if not ResetPWToken.objects.filter(tokenid=tokenid).count():
            break

    tomorrow = timezone.now() + datetime.timedelta(days=1)
    ResetPWToken.objects.filter(user=user).delete()
    ResetPWToken(tokenid=tokenid, expire_time=tomorrow, user=user).save()

    url = '{}/account/password/reset/{}'.format(settings.DOMAIN, tokenid)
    send_mail(ResetPWMessage.title, '',
              'noreply@sso.sparcs.org', [user.email],
              html_message=ResetPWMessage.body.format(url))


# give email auth token to user
def give_email_auth_token(user):
    if user.email.endswith('@sso.sparcs.org'):
        return

    while True:
        tokenid = token_hex(24)
        if not EmailAuthToken.objects.filter(tokenid=tokenid).count():
            break

    tomorrow = timezone.now() + datetime.timedelta(days=1)
    EmailAuthToken.objects.filter(user=user).delete()
    EmailAuthToken(tokenid=tokenid, expire_time=tomorrow, user=user).save()

    url = '{}/account/email/{}'.format(settings.DOMAIN, tokenid)
    send_mail(EmailAuthMessage.title, '',
              'noreply@sso.sparcs.org', [user.email],
              html_message=EmailAuthMessage.body.format(url))


# signup core
def signup_core(post):
    user_f = UserForm(post)
    raw_email = post.get('email', '')

    if not user_f.is_valid() or not validate_email(raw_email):
        return None

    email = user_f.cleaned_data['email']
    password = user_f.cleaned_data['password']
    first_name = user_f.cleaned_data['first_name']
    last_name = user_f.cleaned_data['last_name']
    while True:
        username = token_hex(10)
        if not User.objects.filter(username=username).count():
            break

    user = User.objects.create_user(username=username,
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=email,
                                    password=password)
    user.save()
    UserProfile(user=user, gender='*H').save()

    give_email_auth_token(user)
    return user


# social signup core
def signup_social_core(type, profile):
    while True:
        username = token_hex(10)
        if not User.objects.filter(username=username).count():
            break

    first_name = profile.get('first_name', '')
    last_name = profile.get('last_name', '')

    email = profile.get('email', '')
    if not email:
        email = 'random-{}@sso.sparcs.org'.format(token_hex(6))

    while True:
        if not User.objects.filter(email=email).count():
            break
        email = 'random-{}@sso.sparcs.org'.format(token_hex(6))

    user = User.objects.create_user(username=username,
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=email,
                                    password=token_hex(12))
    user.save()

    user.profile = UserProfile(gender=profile.get('gender', '*H'),
                               password_set=False)
    if 'birthday' in profile:
        user.profile.birthday = profile['birthday']

    if type == 'FB':
        user.profile.facebook_id = profile['userid']
    elif type == 'TW':
        user.profile.twitter_id = profile['userid']
    elif type == 'KAIST':
        user.profile.email_authed = email.endswith('@kaist.ac.kr')
        user.profile.set_kaist_info(profile)
    user.profile.save()
    return user


# Register Service
def reg_service(user, service):
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if m and not m.unregister_time:
        return False
    elif m and m.unregister_time and \
            (timezone.now() - m.unregister_time).days < service.cooltime:
        return False
    elif m:
        m.delete()

    while True:
        sid = token_hex(10)
        if not ServiceMap.objects.filter(sid=sid).count():
            break

    ServiceMap(sid=sid, user=user, service=service,
               register_time=timezone.now(), unregister_time=None).save()
    return True


# Unregister Service
def unreg_service(user, service):
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if not m or m.unregister_time:
        return False

    m.unregister_time = timezone.now()
    m.save()
    return True


# Facebook Init & Auth
def init_fb(callback_url):
    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'auth_type': 'rerequest',
        'scope': 'email',
        'redirect_uri': callback_url,
    }
    return 'https://www.facebook.com/dialog/oauth?{}'.format(urlencode(args))


def auth_fb(code, callback_url):
    # get access token
    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'client_secret': settings.FACEBOOK_APP_SECRET,
        'redirect_uri': callback_url,
        'code': code,
    }
    token_info = parse_qs(requests.get(
        'https://graph.facebook.com/oauth/access_token?',
        params=args, verify=True).text)
    if 'access_token' not in token_info:
        return None, None
    access_token = token_info['access_token'][-1]

    # get grant info
    args = {
        'access_token': access_token
    }
    grant_info = requests.get('https://graph.facebook.com/v2.5/me/permissions',
                              params=args, verify=True).json()
    for data in grant_info["data"]:
        if data["status"] == "declined":
            return None, None

    # get facebook profile
    args = {
        'fields': 'email,first_name,last_name,gender,birthday',
        'access_token': access_token
    }
    fb_info = requests.get('https://graph.facebook.com/v2.5/me',
                           params=args, verify=True).json()
    info = {
        'userid': fb_info['id'],
        'email': fb_info.get('email'),
        'first_name': fb_info.get('first_name'),
        'last_name': fb_info.get('last_name'),
        'gender': parse_gender(fb_info.get('gender')),
        'birthday': fb_info.get('birthday')
    }
    fb_profile = UserProfile.objects.filter(facebook_id=info['userid'],
                                            test_only=False).first()
    return fb_profile, info


# Twitter Init & Auth
tw_consumer = oauth.Consumer(settings.TWITTER_APP_ID,
                             settings.TWITTER_APP_SECRET)
tw_client = oauth.Client(tw_consumer)


def init_tw(callback_url):
    body = 'oauth_callback={}'.format(callback_url)
    resp, content = tw_client.request(
        'https://twitter.com/oauth/request_token', 'POST', body)

    tokens = dict(parse_qsl(content.decode('utf-8')))
    url = 'https://twitter.com/oauth/authenticate?oauth_token={}' \
        .format(tokens['oauth_token'])
    return url, tokens


def auth_tw(tokens, verifier):
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
        'gender': '*H'
    }
    tw_profile = UserProfile.objects.filter(twitter_id=info['userid'],
                                            test_only=False).first()
    return tw_profile, info


# KAIST Auth
kaist_soap_template = (
    '<soapenv:Envelope'
    ' xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
    ' xmlns:ser="http://server.com">'
    '  <soapenv:Header/>'
    '    <soapenv:Body>'
    '      <ser:verification>'
    '        <cookieValue>{}</cookieValue>'
    '        <publicKeyStr>{}</publicKeyStr>'
    '    </ser:verification>'
    '  </soapenv:Body>'
    '</soapenv:Envelope>'
)


def auth_kaist(token):
    payload = kaist_soap_template.format(token, settings.KAIST_APP_SECRET)
    r = requests.post('https://iam.kaist.ac.kr/iamps/services/singlauth/',
                      data=payload, verify=True)
    raw_info = ElementTree.fromstring(r.text)[0][0][0]
    k_info = {}
    for node in raw_info:
        k_info[node.tag] = node.text

    info = {
        'userid': k_info['kaist_uid'],
        'email': k_info.get('mail'),
        'first_name': k_info.get('givenname'),
        'last_name': k_info.get('sn'),
        'gender': '*{}'.format(k_info.get('ku_sex')),
        'birthday': k_info.get('ku_born_date').replace('/', '-'),
        'kaist_info': k_info
    }
    kaist_profile = UserProfile.objects.filter(kaist_id=info['userid'],
                                               test_only=False).first()
    return kaist_profile, info


# Validate reCAPTCHA
def validate_recaptcha(response):
    data = {
        'secret': settings.RECAPTCHA_SECRET,
        'response': response
    }
    resp = requests.post('https://www.google.com/recaptcha/api/siteverify',
                         data=data).json()
    return resp['success']
