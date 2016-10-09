# -*- coding: utf-8 -*-
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.utils import timezone
from apps.core.backends import signup_core, signup_social_core, validate_recaptcha
from apps.core.models import ServiceMap
import datetime
import logging


logger = logging.getLogger('sso.core.account')


# /signup/, # /signup/social/
def signup(request, social=False):
    if request.user.is_authenticated():
        return redirect('/')

    if social and 'info_signup' not in request.session:
        return redirect('/')

    if social:
        info_signup = request.session['info_signup']
        type, profile = info_signup['type'], info_signup['profile']

        email = profile.get('email', '')
        email_warning = email and User.objects.filter(email=email).count()

    if request.method == 'POST':
        if social:
            user = signup_social_core(type, profile)
        else:
            result = validate_recaptcha(request.POST.get('g-recaptcha-response', ''))
            if not result:
                return redirect('/')

            user = signup_core(request.POST)

        if user is None:
            return redirect('/')

        logger.warning('create', {'r': request, 'uid': user.username})

        user.backend = 'django.contrib.auth.backends.ModelBackend'
        auth.login(request, user)

        nexturl = request.session.pop('next', '/')
        return render(request, 'account/signup/done.html',
                      {'type': 'SNS' if social else 'EMAIL', 'nexturl': nexturl})

    if not social:
        return render(request, 'account/signup/main.html')
    return render(request, 'account/signup/sns.html', {'type': type, 'profile': profile,
                                                       'email_warning': email_warning})


# /deactivate/
@login_required
def deactivate(request):
    if request.user.profile.test_only:
        return redirect('/')

    maps = ServiceMap.objects.filter(user=request.user, unregister_time=None)
    ok = len(maps) == 0
    fail = False

    if request.method == 'POST' and ok:
        pw = request.POST.get('password', '')
        if check_password(pw, request.user.password):
            profile = request.user.profile
            profile.expire_time = timezone.now() + datetime.timedelta(days=60)
            profile.save()

            logger.warning('deactivate.success', {'r': request})
            return redirect('/account/logout/')

        fail = True
        logger.warning('deactivate.fail', {'r': request})

    return render(request, 'account/deactivate.html', {'ok': ok, 'fail': fail})
