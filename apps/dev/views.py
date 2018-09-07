import json
import logging
from secrets import token_hex

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import redirect, render

from apps.core.backends import dev_required
from apps.core.forms import ServiceForm
from apps.core.models import Service, UserProfile


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
        logger.info('profile.update', {
            'r': request,
            'extra': [
                ('test', str(profile.test_enabled).lower()),
                ('point', profile.point_test),
            ],
        })

    return render(request, 'dev/main.html', {
        'profile': profile,
        'services': services,
        'users': users,
        'success': success,
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

        service_new.save()

        log_msg = 'create' if not service else 'update'
        logger.warning(f'service.{log_msg}', {
            'r': request,
            'extra': [
                ('name', service_new.name),
                ('alias', service_new.alias),
            ],
        })
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
    logger.warning('service.delete', {
        'r': request,
        'extra': [('name', name)],
    })
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
        else:
            profile = user.profile

        user.first_name = first_name
        user.last_name = last_name
        user.save()

        birthday = request.POST.get('birthday', None)
        profile.gender = request.POST.get('gender', '*H')
        profile.birthday = birthday if birthday else None
        profile.point_test = int(request.POST.get('point_test', '0'))
        profile.save()

        try:
            kaist_info = json.loads(request.POST.get('kaist_info', ''))
            profile.save_kaist_info({
                'userid': kaist_info['kaist_uid'],
                'kaist_info': kaist_info,
            })
        except Exception:
            pass

        log_msg = 'create' if uid == 'add' else 'update'
        logger.warning(f'account.{log_msg}', {
            'r': request,
            'extra': [
                ('uid', user.username),
                ('email', user.email),
            ],
        })
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
    logger.warning('account.delete', {
        'r': request,
        'extra': [('uid', uid)],
    })
    return redirect('/dev/main/')
