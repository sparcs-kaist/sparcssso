from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.signals import (
    user_logged_in, user_logged_out, user_login_failed
)
from django.core.mail import send_mail
from django.dispatch import receiver
from django.utils import timezone
import logging


logger = logging.getLogger('sso.auth')
account_logger = logging.getLogger('sso.account')


@receiver(user_logged_in)
def user_signal_logged_in(sender, request, user, **kwargs):
    logger.info('login.success', {'r': request})

    if not settings.DEBUG and user.is_staff:
        title = '[SPARCS SSO] Staff Login'
        emails = map(lambda x: x[1], settings.ADMINS)
        time = timezone.now()
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        send_mail(
            title, '', 'noreply@sso.sparcs.org', emails,
            html_message=f'time:{time}, id: {user.username}, ip: {ip}'
        )

    if user.profile.activate():
        account_logger.warning('activate', {'r': request})


@receiver(user_logged_out)
def user_signal_logged_out(sender, request, user, **kwargs):
    logger.info('logout', {'r': request})


@receiver(user_login_failed)
def user_signal_login_failed(sender, request, credentials, **kwargs):
    if 'email' in credentials:
        email = credentials['email']
        user = User.objects.filter(email=email).first()
    elif 'user' in credentials:
        user = credentials['user']

    info = f': {email}' if not user else ''
    logger.warning(f'login.fail{info}', {
        'r': request,
        'uid': user.username if user else 'unknown',
    })
