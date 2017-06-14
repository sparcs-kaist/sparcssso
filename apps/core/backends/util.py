import re
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.contrib.auth.models import User


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
    elif not re.match(r'[^@]+@[^@]+', email):
        return False
    elif email.endswith('@sso.sparcs.org'):
        return False
    return User.objects.filter(email=email).count() == 0


# validate reCAPTCHA
def validate_recaptcha(response):
    data = {
        'secret': settings.RECAPTCHA_SECRET,
        'response': response,
    }
    resp = requests.post('https://www.google.com/recaptcha/api/siteverify',
                         data=data).json()
    return resp['success']
