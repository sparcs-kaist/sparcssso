from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone, translation
from apps.core.models import Notice, Statistic, Service
import logging
import json


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


# /stats/
def stats(request):
    level = 0
    if request.user.is_authenticated():
        if request.user.is_staff:
            level = 2
        elif request.user.profile.sparcs_id:
            level = 1

    raw_stats = Statistic.objects.order_by('-time')
    if len(raw_stats) == 0:
        raw_stat = {}
    else:
        time = raw_stats[0].time
        raw_stat = json.loads(raw_stats[0].data)

    stat = []
    for name, value in raw_stat.iteritems():
        if name != 'all':
            service = Service.objects.get(name=name)
            if level < 1 and not service.is_public:
                continue

        s = {}
        s['name'] = name
        s['alias'] = service.alias if name != 'all' else 'all'
        s.update(value)

        if name == 'all':
            stat.insert(0, s)
        else:
            stat.append(s)

    return render(request, 'stats.html', {'level': level, 'time': time, 'stat': stat})


# /help/
def help(request):
    return render(request, 'help.html')


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
