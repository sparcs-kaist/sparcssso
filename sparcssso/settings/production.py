from os import environ

from sparcssso.version import get_version_info

from .common import *  # noqa: F401, F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    'sparcssso.kaist.ac.kr',
    'sso.sparcs.org',
]

VERSION = get_version_info(DEBUG, ALLOWED_HOSTS)

DOMAIN = 'https://sparcssso.kaist.ac.kr'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': environ.get('SSO_DB_NAME'),
        'USER': environ.get('SSO_DB_USER'),
        'PASSWORD': environ.get('SSO_DB_PASSWORD'),
        'HOST': environ.get('SSO_DB_HOST'),
        'PORT': environ.get('SSO_DB_PORT', '3306'),
    },
}

LOGGING['loggers']['django.request'] = {  # noqa: F405
    'handlers': ['mail'],
    'level': 'ERROR',
}

LOG_DIR = '/data/archive/logs/'

LOG_BUFFER_DIR = '/data/archive/buffer/'

STAT_FILE = '/data/archive/stats.txt'
