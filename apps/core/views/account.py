# -*- coding: utf-8 -*-
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import render, redirect
from django.utils import timezone
from apps.core.backends import signup_core
from apps.core.models import ServiceMap
import datetime
import logging


logger = logging.getLogger('sso.core.account')


# /signup/, /signup/social/
def signup(request, is_social=False):
    if request.user.is_authenticated():
        return redirect('/')

    if is_social and 'info_signup' not in request.session:
        return redirect('/')

    signup = request.session.get('info_signup',
            {'type': 'EMAIL', 'profile': {'gender': 'E'}})
    type = signup['type']
    info = signup['profile']

    if request.method == 'POST':
        user = signup_core(request.POST)

        if user is None:
            logger.warning('signup.fail')
            raise SuspiciousOperation()

        if type == 'FB':
            user.profile.facebook_id = info['userid']
        elif type == 'TW':
            user.profile.twitter_id = info['userid']
        elif type == 'KAIST':
            user.profile.set_kaist_info(info)

        user.profile.save()
        request.session.pop('info_signup', None)
        logger.warning('create', request, uid=user.username)
        return render(request, 'account/signup/done.html', {'type': type})

    return render(request, 'account/signup/main.html', {'type': type, 'info': info})


# /deactivate/
@login_required
def deactivate(request):
    maps = ServiceMap.objects.filter(user=request.user, unregister_time=None)
    ok = len(maps) == 0
    fail = False

    if request.method == 'POST' and ok:
        pw = request.POST.get('password', '')
        if check_password(pw, request.user.password):
            profile = request.user.profile
            profile.expire_time = timezone.now() + datetime.timedelta(days=60)
            profile.save()

            logger.warning('deactivate.success', request)
            return redirect('/account/logout/')

        fail = True
        logger.warning('deactivate.fail', request)

    return render(request, 'account/deactivate.html', {'ok': ok, 'fail': fail})

