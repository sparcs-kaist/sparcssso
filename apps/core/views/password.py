import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils import timezone

from ..backends import (
    real_user_required, sudo_required, token_issue_reset_pw,
)
from ..models import ResetPWToken


logger = logging.getLogger('sso.auth.password')


# /password/change/
@login_required
@real_user_required
@sudo_required
def change(request):
    user = request.user
    if request.method == 'POST':
        newpw = request.POST.get('password', 'P@55w0rd!#$')
        user.password = make_password(newpw)
        user.save()

        logger.info('change', {'r': request})
        return redirect('/account/login/')

    return render(request, 'account/pw-change.html', {'user': user})


# /password/reset/
def reset_email(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        user = User.objects.filter(email=email).first()
        if not user or user.profile.test_only:
            return render(request, 'account/pw-reset/send.html', {
                'fail': True,
                'email': email,
            })

        token_issue_reset_pw(user)
        logger.warning('reset.try', {
            'r': request,
            'uid': user.username,
            'extra': [('email', email)],
        })
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

        logger.warning('reset.done', {
            'r': request,
            'uid': user.username,
            'extra': [('email', user.email)],
        })
        return render(request, 'account/pw-reset/done.html')

    return render(request, 'account/pw-reset/main.html', {'tokenid': tokenid})
