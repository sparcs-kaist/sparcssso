from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone, translation
from apps.core.models import Notice, Service
import logging


logger = logging.getLogger('sso')


# /main/
def main(request):
    current_time = timezone.now()
    services = Service.objects.filter(is_public=True)
    notice = Notice.objects.filter(valid_from__lte=current_time,
                                   valid_to__gt=current_time).first()

    return render(request, 'main.html', {'services': services, 'notice': notice})


# /lang/
def lang(request, code):
    if code not in ['en', 'ko']:
        return redirect('/')

    translation.activate(code)
    request.session[translation.LANGUAGE_SESSION_KEY] = code
    return redirect(request.META.get('HTTP_REFERER', '/'))


# /credits/
def credits(request):
    return render(request, 'credits.html')


# /terms/
def terms(request):
    return render(request, 'terms.html')


# /privacy/
def privacy(request):
    return render(request, 'privacy.html')


# /doc/dev/
@login_required
def doc_dev(request):
    user = request.user
    profile = user.profile
    if not user.is_staff and not profile.is_for_test and not profile.sparcs_id:
        return redirect('/')
    return render(request, 'doc.dev.html')


# /doc/sysop/
@login_required
def doc_sysop(request):
    if not request.user.is_staff:
        return redirect('/')
    return render(request, 'doc.sysop.html')
