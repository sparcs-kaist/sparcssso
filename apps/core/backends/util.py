import re
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.contrib.auth.models import User

from apps.core.models import EmailDomain


social_name_map = {
    'FB': 'facebook',
    'TW': 'twitter',
    'KAIST': 'kaist',
}


# {male, female, etc} -> {M, F, E}
def parse_gender(gender):
    if gender == 'male':
        return '*M'
    elif gender == 'female':
        return '*F'
    return gender


# make clean url; / for all external urls
def get_clean_url(url):
    hostname = urlparse(url).hostname
    if hostname:
        return '/'
    return url


# give pretty name for social account
def get_social_name(type):
    return social_name_map.get(type, type)


# check given email is available or not
def validate_email(email, exclude=''):
    if email == exclude:
        return True

    m = re.match(r'^([^@]+)@([^@]+)$', email)
    if not m:
        return False

    domain = m.group(2).strip().lower()
    if domain == 'sso.sparcs.org':
        return False
    elif EmailDomain.objects.filter(domain=domain, is_banned=True).exists():
        return False
    return User.objects.filter(email=email).count() == 0


# validate reCAPTCHA
def validate_recaptcha(response, secret=settings.RECAPTCHA_INVISIBLE_SECRET):
    if not secret:
        return True

    data = {
        'secret': secret,
        'response': response,
    }
    resp = requests.post('https://www.google.com/recaptcha/api/siteverify',
                         data=data).json()
    return resp['success']
