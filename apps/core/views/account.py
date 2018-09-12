import datetime
import logging

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.core.backends import (
    anon_required, get_social_name, real_user_required,
    signup_email, signup_social, sudo_required,
    validate_recaptcha,
)
from apps.core.models import ServiceMap


logger = logging.getLogger('sso.account')


# /signup/, # /signup/social/
@anon_required
def signup(request, social=False):
    if social and 'info_signup' not in request.session:
        return redirect('/')

    if social:
        info_signup = request.session['info_signup']
        typ, profile = info_signup['type'], info_signup['profile']

        email = profile.get('email', '')
        email_warning = email and User.objects.filter(email=email).count()

    if request.method == 'POST':
        if social:
            user = signup_social(typ, profile)
        else:
            captcha_data = request.POST.get('g-recaptcha-response', '')
            result = validate_recaptcha(captcha_data)
            if not result:
                return redirect('/')
            user = signup_email(request.POST)

        if user is None:
            return redirect('/')

        type_str = get_social_name(typ) if social else 'email'
        social_uid = profile['userid'] if social else ''
        logger.warning('create', {
            'r': request,
            'uid': user.username,
            'extra': [
                ('type', type_str),
                ('email', user.email),
                ('uid', social_uid),
                ('name', f'{user.first_name} {user.last_name}'),
            ],
        })
        user = auth.authenticate(request=request, user=user)
        auth.login(request, user)

        nexturl = request.session.pop('next', '/')
        return render(request, 'account/signup/done.html', {
            'type': 'SNS' if social else 'EMAIL',
            'nexturl': nexturl,
        })

    if not social:
        return render(request, 'account/signup/main.html')
    return render(request, 'account/signup/sns.html', {
        'type': typ,
        'profile': profile,
        'email_warning': email_warning,
        'captcha_enabled': 'y' if settings.RECAPTCHA_SECRET else '',
    })


# /deactivate/
@login_required
@real_user_required
@sudo_required
def deactivate(request):
    ok = ServiceMap.objects.filter(
        user=request.user, unregister_time=None,
    ).count() == 0

    if request.method == 'POST' and ok:
        profile = request.user.profile
        profile.expire_time = timezone.now() + datetime.timedelta(days=60)
        profile.save()

        logger.warning('deactivate', {'r': request})

        auth.logout(request)
        return redirect('/')

    return render(request, 'account/deactivate.html', {'ok': ok})
