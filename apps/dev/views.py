from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.http import Http404
from apps.core.models import Service
from apps.core.forms import ServiceForm
import logging
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
    if request.method == 'POST':
        point_test = request.POST.get('point', '0')
        point_test = int(point_test) if point_test.isdigit() else 0
        test_enabled = request.POST.get('test', 'D')

        if profile.flags['sysop']:
            test_enabled = False
        elif profile.flags['test'] and not profile.flags['sparcs']:
            test_enabled = True

        profile.point_test = point_test
        profile.test_enabled = test_enabled
        profile.save()
        success = True

    return render(request, 'dev/main.html', {'profile': profile, 'services': services, 'success': success})


# /doc/
@login_required
def doc(request):
    if not request.user.profile.flags['dev']:
        raise PermissionDenied()
    return render(request, 'dev/doc.html')


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
        if not service:
            while True:
                name = 'test%s' % os.urandom(6).encode('hex')
                if not Service.objects.filter(name=name).count():
                    break

        service_f = ServiceForm(request.POST)
        service = service_f.save(commit=False)
        service.is_shown = False
        service.scope = 'TEST'
        service.admin_user = request.user
        service.name = name
        service.save()

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
    return redirect('/dev/main/')
