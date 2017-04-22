from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from apps.core.backends import (
    token_issue_email_auth, get_social_name, validate_email
)
from apps.core.models import ServiceMap, EmailAuthToken, PointLog, UserLog
from apps.core.forms import UserForm, UserProfileForm
import logging


logger = logging.getLogger('sso.profile')


# /profile/
@login_required
def main(request):
    user = request.user
    profile = user.profile

    result_prof = request.session.pop('result_prof', -1)
    result_con = request.session.pop('result_con', -1)
    if request.method == 'POST':
        user_f = UserForm(request.POST)
        profile_f = UserProfileForm(request.POST, instance=profile)

        if user_f.is_valid() and profile_f.is_valid():
            user.first_name = user_f.cleaned_data['first_name']
            user.last_name = user_f.cleaned_data['last_name']
            user.save()

            profile = profile_f.save()
            result_prof = 1
            logger.info('modify', {'r': request})

    return render(request, 'account/profile.html', {
        'user': user,
        'profile': profile,
        'result_prof': result_prof,
        'result_con': result_con,
        'kaist_enabled': settings.KAIST_APP_ENABLED,
    })


# /disconnect/{fb,tw}/
@login_required
def disconnect(request, type):
    if request.method != 'POST':
        return redirect('/account/profile/')

    uid = ''
    profile = request.user.profile
    if profile.test_only:
        return redirect('/account/profile/')

    if type == 'FB':
        uid = profile.facebook_id
        profile.facebook_id = ''
    elif type == 'TW':
        uid = profile.twitter_id
        profile.twitter_id = ''

    if not profile.user.has_usable_password() and \
       not (profile.facebook_id or profile.twitter_id or profile.kaist_id):
        request.session['result_con'] = 4
        return redirect('/account/profile/')

    profile.save()

    type_str = get_social_name(type)
    logger.warning('social.disconnect: type={},id={}'.format(
        type_str, uid), {'r': request})

    request.session['result_con'] = 5
    return redirect('/account/profile/')


# /email/change/
@login_required
def email(request):
    user, profile = request.user, request.user.profile
    if profile.test_only:
        return redirect('/')

    if request.method == 'POST':
        email_new = request.POST.get('email', '').lower()
        if validate_email(email_new):
            if profile.email_authed:
                profile.email_new = email_new
                profile.save()
            else:
                user.email = email_new
                user.save()
            token_issue_email_auth(user)
            request.session['result_email'] = 4
        else:
            request.session['result_email'] = 3

    result_email = request.session.pop('result_email', -1)
    return render(request, 'account/email.html', {
        'user': request.user,
        'result_email': result_email,
    })


# /email/verify/
@login_required
def email_resend(request):
    user, profile = request.user, request.user.profile
    if request.method != 'POST':
        return redirect('/account/email/change/')
    elif profile.email_authed and not profile.email_new:
        return redirect('/account/email/change/')

    token_issue_email_auth(user)
    logger.info('email.resend', {'r': request})
    request.session['result_email'] = 5

    return redirect('/account/email/change/')


# /email/verify/<tokenid>
@login_required
def email_verify(request, tokenid):
    user, profile = request.user, request.user.profile
    if profile.test_only:
        return redirect('/')

    token = EmailAuthToken.objects.filter(tokenid=tokenid).first()
    if not token:
        request.session['result_email'] = 2
        return redirect('/account/email/change/')
    elif token.expire_time < timezone.now():
        token.delete()
        request.session['result_email'] = 2
        return redirect('/account/email/change/')
    elif token.user != user:
        return redirect('/account/email/change/')

    if profile.email_authed:
        user.email = profile.email_new
        profile.email_new = ''
    else:
        profile.email_authed = True

    if user.email.endswith('@sparcs.org'):
        profile.sparcs_id = user.email.split('@')[0]
    profile.save()
    user.save()
    token.delete()

    request.session['result_email'] = 1
    logger.info('email.done', {'r': request})
    return redirect('/account/email/change/')


# /service/
@login_required
def service(request):
    maps = ServiceMap.objects.filter(user=request.user, unregister_time=None)
    return render(request, 'account/service.html', {
        'user': request.user,
        'maps': maps
    })


# /point/
@login_required
def point(request):
    logs = PointLog.objects.filter(user=request.user).order_by('-time')
    return render(request, 'account/point.html', {
        'user': request.user,
        'logs': logs,
    })


# /log/
@login_required
def log(request):
    logs = UserLog.objects.filter(user=request.user,
                                  hide=False).order_by('-time')
    return render(request, 'account/log.html', {'logs': logs})
