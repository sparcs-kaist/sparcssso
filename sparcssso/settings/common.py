import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.api',
    'apps.core',
    'apps.dev',
    'apps.web',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'apps.core.backends.EmailLoginBackend',
    'apps.core.backends.LDAPLoginBackend',
    'apps.core.backends.PasswordlessLoginBackend',
]

ROOT_URLCONF = 'sparcssso.urls'

TEMPLATES = [{
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
}]

WSGI_APPLICATION = 'sparcssso.wsgi.application'

LOGIN_URL = '/account/login/'


# Security
CSRF_USE_SESSIONS = True

CSRF_FAILURE_VIEW = 'apps.core.views.general.csrf_failure'


# Facebook, Twitter, KAIST API keys

FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID', '')

FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET', '')

TWITTER_APP_ID = os.environ.get('TWITTER_APP_ID', '')

TWITTER_APP_SECRET = os.environ.get('TWITTER_APP_SECRET', '')

KAIST_APP_ENABLED = True if os.environ.get('KAIST_APP_ENABLED', '0') == '1' else False

KAIST_APP_SECRET = os.environ.get('KAIST_APP_SECRET', '')

RECAPTCHA_SECRET = os.environ.get('RECAPTCHA_SECRET', '')

KAIST_V2_HOSTNAME = os.environ.get('KAIST_V2_HOSTNAME', 'sso.kaist.ac.kr')

KAIST_V2_CLIENT_ID = os.environ.get('KAIST_V2_CLIENT_ID', 'kaist-sparcs')

KAIST_V2_CLIENT_SECRET = os.environ.get('KAIST_V2_CLIENT_SECRET', '')


# E-mail settings
EMAIL_HOST = 'localhost'
EMAIL_PORT = int(os.environ.get('SSO_EMAIL_PORT', '25'))

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = []


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('SSO_DB_NAME'),
        'USER': os.environ.get('SSO_DB_USER'),
        'PASSWORD': os.environ.get('SSO_DB_PASSWORD'),
        'HOST': os.environ.get('SSO_DB_HOST'),
        'PORT': os.environ.get('SSO_DB_PORT', '3306'),
    },
}


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

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
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Admins & Logging
TEAM_EMAILS = ['sso@sparcs.org']

ADMINS = (('SSO SYSOP', 'sso.sysop@sparcs.org'),)


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

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
if SENTRY_DSN != '':
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        send_default_pii=True,
    )
else:
    print('SENTRY_DSN not provided. Metrics will not be sent.')  # noqa: T001
