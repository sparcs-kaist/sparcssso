from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.utils import timezone
from apps.core.backends import (
    anon_required, real_user_required, sudo_required,
    signup_email, signup_social, validate_recaptcha,
)
from apps.core.models import ServiceMap
import datetime
import logging


logger = logging.getLogger('sso.core.account')


# /signup/, # /signup/social/
@anon_required
def signup(request, social=False):
    if social and 'info_signup' not in request.session:
        return redirect('/')

    if social:
        info_signup = request.session['info_signup']
        type, profile = info_signup['type'], info_signup['profile']

        email = profile.get('email', '')
        email_warning = email and User.objects.filter(email=email).count()

    if request.method == 'POST':
        if social:
            user = signup_social(type, profile)
        else:
            captcha_data = request.POST.get('g-recaptcha-response', '')
            result = validate_recaptcha(captcha_data)
            if not result:
                return redirect('/')
            user = signup_email(request.POST)

        if user is None:
            return redirect('/')

        logger.warning('create', {'r': request, 'uid': user.username})
        user = auth.authenticate(request=request, user=user)
        auth.login(request, user)

        nexturl = request.session.pop('next', '/')
        return render(request, 'account/signup/done.html', {
            'type': 'SNS' if social else 'EMAIL',
            'nexturl': nexturl
        })

    if not social:
        return render(request, 'account/signup/main.html')
    return render(request, 'account/signup/sns.html', {
        'type': type,
        'profile': profile,
        'email_warning': email_warning
    })


# /deactivate/
@login_required
@real_user_required
@sudo_required
def deactivate(request):
    maps = ServiceMap.objects.filter(user=request.user, unregister_time=None)
    ok = len(maps) == 0

    if request.method == 'POST' and ok:
        profile = request.user.profile
        profile.expire_time = timezone.now() + datetime.timedelta(days=60)
        profile.save()

        logger.warning('deactivate.success', {'r': request})

        auth.logout(request)
        return redirect('/')

    return render(request, 'account/deactivate.html', {'ok': ok})
