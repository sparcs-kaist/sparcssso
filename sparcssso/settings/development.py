import os

from sparcssso.version import get_version_info

from .common import *  # noqa: F401, F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DOMAIN = os.environ.get('SSO_DOMAIN', 'https://sso.dev.sparcs.org')

ALLOWED_HOSTS = [
    'sso.dev.sparcs.org',
    'localhost',
]

_DOMAIN_WITHOUT_SCHEME = DOMAIN.replace("https://", "").replace("http://", "")
if _DOMAIN_WITHOUT_SCHEME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS += [_DOMAIN_WITHOUT_SCHEME]

if os.environ.get('SSO_LOCAL', '0') == '1':
    ALLOWED_HOSTS += ['localhost']

VERSION = get_version_info(DEBUG, ALLOWED_HOSTS)


LOG_DIR = os.path.join(BASE_DIR, 'archive/logs/')  # noqa: F405
LOG_BUFFER_DIR = os.path.join(BASE_DIR, 'archive/buffer/')  # noqa: F405

STAT_FILE = os.path.join(BASE_DIR, 'archive/stats.txt')  # noqa: F405

KAIST_APP_V2_HOSTNAME = os.environ.get('KAIST_APP_V2_HOSTNAME', 'ssodev.kaist.ac.kr')
