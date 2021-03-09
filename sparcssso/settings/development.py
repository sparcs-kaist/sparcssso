import os

from sparcssso.version import get_version_info

from .common import *  # noqa: F401, F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'ssodev.sparcs.org',
    'localhost'
]

if os.environ.get('SSO_LOCAL', '0') == '1':
    ALLOWED_HOSTS += ['localhost']

VERSION = get_version_info(DEBUG, ALLOWED_HOSTS)

DOMAIN = 'http://ssodev.sparcs.org'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),  # noqa: F405
    },
}

LOG_DIR = os.path.join(BASE_DIR, 'archive/logs/')  # noqa: F405
LOG_BUFFER_DIR = os.path.join(BASE_DIR, 'archive/buffer/')  # noqa: F405

STAT_FILE = os.path.join(BASE_DIR, 'archive/stats.txt')  # noqa: F405
