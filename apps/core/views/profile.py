import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.backends import (
    get_social_name, real_user_required, service_unregister,
    sudo_required, token_issue_email_auth, validate_email,
)
from apps.core.constants import EmailVerificationResult, SocialConnectResult
from apps.core.forms import UserForm, UserProfileForm
from apps.core.models import EmailAuthToken, PointLog, ServiceMap, UserLog


logger = logging.getLogger('sso.profile')
service_logger = logging.getLogger('sso.service')


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

            if profile.birthday:
                birthday_str = profile.birthday.isoformat()
            else:
                birthday_str = ''
            logger.info('update', {
                'r': request,
                'extra': [
                    ('name', f'{user.first_name} {user.last_name}'),
                    ('gender', profile.gender),
                    ('birthday', birthday_str),
                ],
            })

    return render(request, 'account/profile.html', {
        'user': user,
        'profile': profile,
        'result_prof': result_prof,
        'result_con': result_con,
        'kaist_enabled': settings.KAIST_APP_ENABLED,
    })


# /disconnect/{fb,tw}/
@require_POST
@login_required
def disconnect(request, site):
    uid = ''
    profile = request.user.profile
    if profile.test_only:
        result_code = SocialConnectResult.TEST_ONLY
        return HttpResponseRedirect(f'/account/profile/?connect_site={site}&connect_result={result_code.name}')

    result_code = SocialConnectResult.DISCONNECT_SUCCESS
    if site == 'FB':
        uid = profile.facebook_id
        profile.facebook_id = ''
    elif site == 'TW':
        uid = profile.twitter_id
        profile.twitter_id = ''

    has_social = (
        profile.facebook_id or
        profile.twitter_id or
        profile.kaist_id
    )
    if not profile.user.has_usable_password() and not has_social:
        result_code = SocialConnectResult.ONLY_CONNECTION
    else:
        profile.save()
        logger.warning('social.disconnect', {
            'r': request,
            'extra': [
                ('type', get_social_name(site)),
                ('uid', uid),
            ],
        })
    request.session['result_con'] = result_code.value
    return HttpResponseRedirect(f'/account/profile/?connect_site={site}&connect_result={result_code.name}')


# /email/change/
@login_required
@real_user_required
@sudo_required
def email(request):
    user, profile = request.user, request.user.profile
    if request.method == 'POST':
        email_new = request.POST.get('email', '').lower()
        if validate_email(email_new):
            if profile.email_authed:
                profile.email_new = email_new
                profile.save()
            else:
                user.email = email_new
                user.save()

            log_msg = 'try' if profile.email_authed else 'done'
            logger.warning(f'email.update.{log_msg}', {
                'r': request,
                'extra': [('email', email_new)],
            })
            token_issue_email_auth(user)
            request.session['result_email'] = EmailVerificationResult.UPDATED.value
        else:
            request.session['result_email'] = EmailVerificationResult.EMAIL_IN_USE.value

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
    request.session['result_email'] = EmailVerificationResult.SENT.value

    return redirect('/account/email/change/')


# /email/verify/<tokenid>
@login_required
@real_user_required
def email_verify(request, tokenid):
    user, profile = request.user, request.user.profile
    token = EmailAuthToken.objects.filter(tokenid=tokenid).first()
    if not token:
        request.session['result_email'] = EmailVerificationResult.TOKEN_INVAILD.value
        return redirect('/account/email/change/')
    elif token.expire_time < timezone.now():
        token.delete()
        request.session['result_email'] = EmailVerificationResult.TOKEN_INVAILD.value
        return redirect('/account/email/change/')
    elif token.user != user:
        return redirect('/account/email/change/')

    email = profile.email_new if profile.email_authed else user.email
    logger.warning('email.verify', {
        'r': request,
        'extra': [('email', email)],
    })
    if profile.email_authed:
        user.email = profile.email_new
        profile.email_new = ''
        logger.warning('email.update.done', {
            'r': request,
            'extra': [('email', user.email)],
        })
    else:
        profile.email_authed = True

    if user.email.endswith('@sparcs.org'):
        profile.sparcs_id = user.email.split('@')[0]
    profile.save()
    user.save()
    token.delete()

    request.session['result_email'] = EmailVerificationResult.SUCCESS.value
    return redirect('/account/email/change/')


# /service/
@login_required
@sudo_required
def service(request):
    maps = ServiceMap.objects.filter(user=request.user, unregister_time=None)
    if request.method == 'POST':
        name = request.POST.get('name', '')
        map_obj = maps.filter(service__name=name).first()
        if not map_obj:
            return redirect('/account/service/')

        result = service_unregister(map_obj)
        log_msg = 'success' if result.get('success', False) else 'fail'
        service_logger.warning(f'unregister.{log_msg}', {
            'r': request,
            'extra': [
                ('app', name),
                ('sid', map_obj.sid),
            ],
        })
        request.session['result_service'] = result

    result_service = request.session.pop('result_service', {})
    return render(request, 'account/service.html', {
        'user': request.user,
        'maps': maps,
        'result_service': result_service,
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
@sudo_required
def log(request):
    logs = UserLog.objects.filter(
        user=request.user, hide=False,
    ).order_by('-time')
    return render(request, 'account/log.html', {'logs': logs})
