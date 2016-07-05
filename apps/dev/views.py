from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.http import Http404
import logging


logger = logging.getLogger('sso.dev')


# /main/
@login_required
def main(request):
    if not request.user.profile.flags['dev']:
        raise PermissionDenied()

    profile = request.user.profile
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

        return render(request, 'dev/main.html', {'profile': profile, 'success': True})

    return render(request, 'dev/main.html', {'profile': profile})


# /doc/
@login_required
def doc(request):
    if not request.user.profile.flags['dev']:
        raise PermissionDenied()
    return render(request, 'dev/doc.html')


# /service/(id)/
@login_required
def service(request, sid):
    pass

