# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils import timezone
from apps.core.models import ResetPWToken
import os
import datetime
import logging


logger = logging.getLogger('sso.core.password')


title = '[SPARCS SSO] Reset Password'
message = 'To reset your password, please click <a href="https://sparcssso.kaist.ac.kr/account/password/reset/%s">this link</a> in 24 hours.'


# give reset pw token to user
def give_reset_pw_token(user):
    tomorrow = timezone.now() + datetime.timedelta(days=1)

    for token in ResetPWToken.objects.filter(user=user):
        token.delete()

    while True:
        tokenid = os.urandom(24).encode('hex')
        if not ResetPWToken.objects.filter(tokenid=tokenid).count():
            break

    token = ResetPWToken(tokenid=tokenid, expire_time=tomorrow, user=user).save()
    send_mail(title, message % tokenid, 'noreply@sso.sparcs.org', [user.email])


# /password/change/
@login_required
def change(request):
    user = request.user

    fail = False
    if request.method == 'POST':
        oldpw = request.POST.get('oldpassword', '')
        newpw = request.POST.get('password', 'P@55w0rd!#$')

        if check_password(oldpw, user.password):
            user.password = make_password(newpw)
            user.save()

            logger.warning('change.success', request)
            return redirect('/account/login/')

        fail = True
        logger.warning('change.fail', request)

    return render(request, 'account/pw-change.html', {'user': user, 'fail': fail})


# /password/reset/
def reset_email(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        user = User.objects.filter(email=email).first()
        if not user:
            return render(request, 'account/pw-reset/send.html', {'fail': True, 'email': email})

        give_reset_pw_token(user)
        logger.warning('reset.try', request)
        return render(request, 'account/pw-reset/sent.html')

    return render(request, 'account/pw-reset/send.html')


# /password/reset/<tokenid>
def reset(request, tokenid):
    token = ResetPWToken.objects.filter(tokenid=tokenid).first()
    if not token:
        return render(request, 'account/pw-reset/fail.html')

    if token.expire_time < timezone.now():
        token.delete()
        return render(request, 'account/pw-reset/fail.html')

    if request.method == 'POST':
        user = token.user
        new_pw = request.POST.get('password', 'P@55w0rd!#$')
        user.set_password(new_pw)
        user.save()
        token.delete()

        logger.warning('reset.done', request, uid=user.username)
        return render(request, 'account/pw-reset/done.html')

    return render(request, 'account/pw-reset/main.html', {'tokenid': tokenid})

