from django.conf import settings
from django.shortcuts import render, redirect
from django.utils import timezone, translation
from django.core.mail import send_mail
from apps.core.backends import validate_recaptcha
from apps.core.models import Notice, Statistic, Document, Service
import logging
import json


logger = logging.getLogger('sso')


def _get_document(category, version=''):
    docs = list(Document.objects.filter(category=category).order_by('-date_apply'))
    if len(docs) == 0:
        return None, '', '', ''

    prev_i, next_i, cur_i = -1, -1, -1
    if version:
        for i in range(len(docs)):
            if docs[i].version == version:
                prev_i, next_i, cur_i = i + 1, i - 1, i
                break

        if cur_i == -1:
            return None, '', '', ''
    else:
        prev_i, next_i, cur_i = 1, -1, 0

    prev_v = docs[prev_i].version if prev_i < len(docs) else ''
    next_v = docs[next_i].version if next_i > -1 else ''

    status = 'old'
    if docs[cur_i].date_apply > timezone.now():
        status = 'future'
    elif next_i == -1 or (docs[next_i].date_apply > timezone.now() and cur_i == 1):
        status = 'current'
    return docs[cur_i], status, prev_v, next_v


# /main/
def main(request):
    current_time = timezone.now()
    services = Service.objects.filter(is_shown=True, icon__isnull=False)
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


# /terms/{{version}}/
def terms(request, version=''):
    term, status, prev_v, next_v = _get_document('TERMS', version)
    if not term:
        return redirect('/')

    return render(request, 'terms.html', {'term': term, 'status': status,
                                          'prev_v': prev_v, 'next_v': next_v,
                                          'now': timezone.now()})


# /privacy/{{version}}/
def privacy(request, version=''):
    privacy, status, prev_v, next_v = _get_document('PRIVACY', version)
    if not privacy:
        return redirect('/')

    return render(request, 'privacy.html', {'privacy': privacy, 'status': status,
                                            'prev_v': prev_v, 'next_v': next_v,
                                            'now': timezone.now()})


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
            if level < 1 and not service.is_shown:
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


# /contact/
def contact(request):
    submitted = False
    if request.method == 'POST':
        topic = request.POST.get('topic', '')
        name = request.POST.get('name', '')
        sender = request.POST.get('email', '')
        message = request.POST.get('message', '')
        result = validate_recaptcha(request.POST.get('g-recaptcha-response',''))

        if topic and name and sender and message and result:
            subject = "[SPARCS SSO Report] %s (by %s)" % (topic, name)
            send_mail(subject, message, sender, settings.TEAM_EMAILS)
            submitted = True

    return render(request, 'contact.html', {'submitted': submitted})
