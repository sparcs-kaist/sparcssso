from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.http import Http404
from apps.core.models import Service, UserProfile
from apps.core.forms import ServiceForm
import logging
import json
import os


logger = logging.getLogger('sso.dev')


# /main/
@login_required
def main(request):
    if not request.user.profile.flags['dev']:
        raise PermissionDenied()

    success = False
    profile = request.user.profile
    services = request.user.managed_services.filter(scope='TEST')
    users = User.objects.filter(profile__test_only=True)

    if request.method == 'POST':
        point_test = request.POST.get('point', '0')
        point_test = int(point_test) if point_test.isdigit() else 0
        test_enabled = request.POST.get('test', 'D') == 'E'

        if profile.flags['sysop']:
            test_enabled = False
        elif profile.flags['test'] and not profile.flags['sparcs']:
            test_enabled = True

        profile.point_test = point_test
        profile.test_enabled = test_enabled
        profile.save()
        success = True
        logger.info('profile.modify', {'r': request})

    return render(request, 'dev/main.html', {'profile': profile, 'services': services,
                                             'users': users, 'success': success})


# /service/(name)/
@login_required
def service(request, name):
    if not request.user.profile.flags['dev']:
        raise PermissionDenied()

    service = Service.objects.filter(name=name, scope='TEST').first()
    if (service and service.admin_user != request.user) or \
            (not service and name != 'add'):
        raise Http404

    if request.method == 'POST':
        service_f = ServiceForm(request.POST, instance=service)
        service_new = service_f.save(commit=False)

        if not service:
            while True:
                name = 'test%s' % os.urandom(6).encode('hex')
                if not Service.objects.filter(name=name).count():
                    break

            service_new.name = name
            service_new.is_shown = False
            service_new.scope = 'TEST'
            service_new.secret_key = os.urandom(10).encode('hex')
            service_new.admin_user = request.user
            logger.warn('service.create: name=%s' % name, {'r': request})
        else:
            logger.info('service.modify: name=%s' % name, {'r': request})
        service_new.save()

        return redirect('/dev/main/')

    return render(request, 'dev/service.html', {'service': service})


# /service/(name)/delete/
@login_required
def service_delete(request, name):
    if not request.user.profile.flags['dev']:
        raise PermissionDenied()

    service = Service.objects.filter(name=name, scope='TEST').first()
    if not service or service.admin_user != request.user:
        raise Http404

    service.delete()
    logger.warn('service.delete: name=%s' % name, {'r': request})
    return redirect('/dev/main/')


# /user/(uid)/
@login_required
def user(request, uid):
    if not request.user.profile.flags['dev']:
        raise PermissionDenied()

    user = User.objects.filter(username=uid, profile__test_only=True).first()
    if not user and uid != 'add':
        raise Http404

    if request.method == 'POST':
        first_name = request.POST.get('first_name', 'TEST')
        last_name = request.POST.get('last_name', 'TEST')
        gender = request.POST.get('gender', '*H')
        birthday = request.POST.get('birthday', None)
        if not birthday:
            birthday = None
        test_point = int(request.POST.get('test_point', '0'))
        try:
            kaist_info = json.loads(request.POST.get('kaist_info', ''))
            kaist_id = kaist_info['kaist_uid']
        except:
            kaist_info = {}
            kaist_id = ""

        if not user:
            while True:
                seed = os.urandom(4).encode('hex')
                email = 'test-%s@sso.sparcs.org' % seed
                if not User.objects.filter(email=email).count():
                    break

            while True:
                username = 'test%s' % os.urandom(8).encode('hex')
                if not User.objects.filter(username=username).count():
                    break

            user = User.objects.create_user(username=username,
                                            first_name=first_name,
                                            last_name=last_name,
                                            email=email,
                                            password=seed)
            profile = UserProfile(user=user, email_authed=True,
                                  test_enabled=True, test_only=True)
            logger.warn('user.create: uid=%s' % username, {'r': request})
        else:
            profile = user.profile
            logger.info('user.modify: uid=%s' % uid, {'r': request})

        user.first_name = first_name
        user.last_name = last_name
        user.save()

        profile.gender = gender
        profile.birthday = birthday
        profile.test_point = test_point
        profile.set_kaist_info({'userid': kaist_id, 'kaist_info': kaist_info})
        profile.save()

        return redirect('/dev/main/')

    return render(request, 'dev/user.html', {'tuser': user})


# /user/(uid)/delete/
@login_required
def user_delete(request, uid):
    if not request.user.profile.flags['dev']:
        raise PermissionDenied()

    user = User.objects.filter(username=uid, profile__test_only=True).first()
    if not user:
        raise Http404

    user.delete()
    logger.warn('user.delete: uid=%s' % uid, {'r': request})
    return redirect('/dev/main/')
