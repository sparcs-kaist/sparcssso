import os

from sparcssso.version import get_version_info

from .common import *  # noqa: F401, F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'ssodev.sparcs.org',
    'localhost',
]

if os.environ.get('SSO_LOCAL', '0') == '1':
    ALLOWED_HOSTS += ['localhost']

VERSION = get_version_info(DEBUG, ALLOWED_HOSTS)

DOMAIN = 'https://ssodev.sparcs.org'

LOG_DIR = os.path.join(BASE_DIR, 'archive/logs/')  # noqa: F405
LOG_BUFFER_DIR = os.path.join(BASE_DIR, 'archive/buffer/')  # noqa: F405

STAT_FILE = os.path.join(BASE_DIR, 'archive/stats.txt')  # noqa: F405

KAIST_APP_V2_HOSTNAME = 'ssodev.kaist.ac.kr'
