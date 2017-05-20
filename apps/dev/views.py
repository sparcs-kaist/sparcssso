from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import Http404
from apps.core.backends import dev_required
from apps.core.models import Service, UserProfile
from apps.core.forms import ServiceForm
from secrets import token_hex
import logging
import json


logger = logging.getLogger('sso.dev')


# /main/
@login_required
@dev_required
def main(request):
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

    return render(request, 'dev/main.html', {
        'profile': profile,
        'services': services,
        'users': users,
        'success': success
    })


# /service/(name)/
@login_required
@dev_required
def service(request, name):
    service = Service.objects.filter(name=name, scope='TEST').first()
    if (service and service.admin_user != request.user) or \
            (not service and name != 'add'):
        raise Http404

    if request.method == 'POST':
        service_f = ServiceForm(request.POST, instance=service)
        service_new = service_f.save(commit=False)

        if not service:
            while True:
                name = f'test{token_hex(10)}'
                if not Service.objects.filter(name=name).count():
                    break

            service_new.name = name
            service_new.is_shown = False
            service_new.scope = 'TEST'
            service_new.secret_key = token_hex(10)
            service_new.admin_user = request.user
            logger.warn(f'service.create: name={name}', {'r': request})
        else:
            logger.info(f'service.modify: name={name}', {'r': request})
        service_new.save()

        return redirect('/dev/main/')

    return render(request, 'dev/service.html', {'service': service})


# /service/(name)/delete/
@login_required
@dev_required
def service_delete(request, name):
    service = Service.objects.filter(name=name, scope='TEST').first()
    if not service or service.admin_user != request.user:
        raise Http404

    service.delete()
    logger.warn(f'service.delete: name={name}', {'r': request})
    return redirect('/dev/main/')


# /user/(uid)/
@login_required
@dev_required
def user(request, uid):
    user = User.objects.filter(username=uid, profile__test_only=True).first()
    if not user and uid != 'add':
        raise Http404

    if request.method == 'POST':
        first_name = request.POST.get('first_name', 'TEST')
        last_name = request.POST.get('last_name', 'TEST')

        if not user:
            while True:
                seed = token_hex(4)
                email = f'test-{seed}@sso.sparcs.org'
                if not User.objects.filter(email=email).count():
                    break

            while True:
                username = f'test{token_hex(10)}'
                if not User.objects.filter(username=username).count():
                    break

            user = User.objects.create_user(username=username,
                                            first_name=first_name,
                                            last_name=last_name,
                                            email=email,
                                            password=seed)
            profile = UserProfile(user=user, email_authed=True,
                                  test_enabled=True, test_only=True)
            logger.warn(f'user.create: uid={username}', {'r': request})
        else:
            profile = user.profile
            logger.info(f'user.modify: uid={uid}', {'r': request})

        user.first_name = first_name
        user.last_name = last_name
        user.save()

        birthday = request.POST.get('birthday', None)
        if not birthday:
            birthday = None
        profile.gender = request.POST.get('gender', '*H')
        profile.birthday = request.POST.get('birthday', None)
        profile.point_test = int(request.POST.get('point_test', '0'))
        profile.save()

        try:
            kaist_info = json.loads(request.POST.get('kaist_info', ''))
            profile.save_kaist_info({
                'userid': kaist_info['kaist_uid'],
                'kaist_info': kaist_info,
            })
        except:
            pass
        return redirect('/dev/main/')

    return render(request, 'dev/user.html', {'tuser': user})


# /user/(uid)/delete/
@login_required
@dev_required
def user_delete(request, uid):
    user = User.objects.filter(username=uid, profile__test_only=True).first()
    if not user:
        raise Http404

    user.delete()
    logger.warn(f'user.delete: uid={uid}', {'r': request})
    return redirect('/dev/main/')
