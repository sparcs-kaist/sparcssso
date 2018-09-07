"""
Django settings for sparcssso project.

Generated by 'django-admin startproject' using Django 1.8.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

from sparcssso.version import get_version_info


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'r#f-7qnrv40bl+(wkmin6)u7mez#s$7^+8zo%k^+_sm^vw+95p'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'ssodev.sparcs.org',
]

DOMAIN = 'http://ssodev.sparcs.org'

VERSION = get_version_info()


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.api',
    'apps.core',
    'apps.dev',
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

AUTHENTICATION_BACKENDS = [
    'apps.core.backends.EmailLoginBackend',
    'apps.core.backends.LDAPLoginBackend',
    'apps.core.backends.PasswordlessLoginBackend',
]

ROOT_URLCONF = 'sparcssso.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.backends.context_processors.version',
            ],
        },
    },
]

WSGI_APPLICATION = 'sparcssso.wsgi.application'

LOGIN_URL = '/account/login/'


# Security
CSRF_USE_SESSIONS = True

CSRF_FAILURE_VIEW = 'apps.core.views.general.csrf_failure'


# Facebook, Twitter, KAIST API keys

FACEBOOK_APP_ID = ''

FACEBOOK_APP_SECRET = ''

TWITTER_APP_ID = ''

TWITTER_APP_SECRET = ''

KAIST_APP_ENABLED = False

KAIST_APP_SECRET = ''

RECAPTCHA_SECRET = ''


# E-mail settings
EMAIL_HOST = 'localhost'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGES = (
    ('en', 'English'),
    ('ko', '한국어'),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Admins & Logging
TEAM_EMAILS = ['sso@sparcs.org', ]

ADMINS = (('SSO SYSOP', 'sso.sysop@sparcs.org'),)

LOG_DIR = os.path.join(BASE_DIR, 'archive/logs/')

LOG_BUFFER_DIR = os.path.join(BASE_DIR, 'archive/buffer/')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'apps.logger.SSOLogHandler',
        },
        'mail': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'loggers': {
        'sso': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}

STAT_FILE = os.path.join(BASE_DIR, 'archive/stats.txt')


# Local Settings
try:
    from .local_settings import * # noqa: F401, F403
except ImportError:
    pass
