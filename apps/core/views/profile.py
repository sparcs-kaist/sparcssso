# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from apps.core.backends import unreg_service
from apps.core.models import Service, ServiceMap, PointLog, UserLog
from apps.core.forms import UserForm, UserProfileForm
import logging


logger = logging.getLogger('sso.core.profile')


# /profile/
@login_required
def main(request):
    user = request.user
    profile = user.profile

    success = False
    result_con = request.session.pop('result_con', -1)
    if request.method == 'POST':
        user_f = UserForm(request.POST)
        profile_f = UserProfileForm(request.POST, instance=profile)

        if user_f.is_valid() and profile_f.is_valid():
            user.first_name = user_f.cleaned_data['first_name']
            user.last_name = user_f.cleaned_data['last_name']
            user.save()

            profile = profile_f.save()
            success = True
            logger.info('modify', {'r': request})

    return render(request, 'account/profile.html',
                  {'user': user, 'profile': profile,
                   'success': success, 'result_con': result_con})


# /disconnect/{fb,tw}/
@login_required
def disconnect(request, type):
    if request.method != 'POST':
        return redirect('/account/profile/')

    uid = ''
    profile = request.user.profile
    if type == 'FB':
        uid = profile.facebook_id
        profile.facebook_id = ''
    elif type == 'TW':
        uid = profile.twitter_id
        profile.twitter_id = ''
    profile.save()

    request.session['result_con'] = 5
    logger.info('disconnect: type=%s,id=%s' % (type.lower(), uid), {'r': request})
    return redirect('/account/profile/')


# /test/toggle/
@login_required
def toggle_test(request):
    profile = request.user.profile
    if request.method == 'POST' and profile.sparcs_id:
        profile.is_for_test = not profile.is_for_test
        profile.save()
    return redirect('/account/profile/')


# /unregister/
@login_required
def unregister(request):
    if request.method != 'POST':
        return redirect('/account/service/')

    name = request.POST.get('app', '')
    service = Service.objects.filter(name=name).first()
    if service:
        result = unreg_service(request.user, service)
        code = 0
        if result:
            logger.info('unregister.success: name=%s' % service.name, {'r': request})
        else:
            code = 1
            logger.warning('unregister.fail: name=%s' % service.name, {'r': request})
        request.session['result_unreg'] = code

    return redirect('/account/service/')


# /service/
@login_required
def service(request):
    user = request.user
    maps = ServiceMap.objects.filter(user=user, unregister_time=None)

    result_unreg = request.session.pop('result_unreg', -1)
    return render(request, 'account/service.html',
                  {'user': user, 'maps': maps, 'result_unreg': result_unreg})


# /point/
@login_required
def point(request):
    user = request.user
    logs = PointLog.objects.filter(user=user).order_by('-time')
    return render(request, 'account/point.html', {'user': user, 'logs': logs})


# /log/
@login_required
def log(request):
    logs = UserLog.objects.filter(user=request.user).order_by('-time')
    return render(request, 'account/log.html', {'logs': logs})
