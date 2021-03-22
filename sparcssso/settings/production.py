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

LOGGING['loggers']['django.request'] = {  # noqa: F405
    'handlers': ['mail'],
    'level': 'ERROR',
}

LOG_DIR = '/data/archive/logs/'

LOG_BUFFER_DIR = '/data/archive/buffer/'

STAT_FILE = '/data/archive/stats.txt'
