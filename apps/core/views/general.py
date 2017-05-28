from django.conf import settings
from django.shortcuts import render, redirect
from django.utils import timezone, translation
from django.core.mail import send_mail
from apps.core.backends import validate_recaptcha
from apps.core.models import Notice, Statistic, Document, Service
import json


def _get_document(category, version=''):
    docs = Document.objects.filter(category=category).order_by('-date_apply')
    if not len(docs):
        return None, '', '', ''

    index = 0
    if version:
        for i, doc in enumerate(docs):
            if doc.version == version:
                index = i
                break
        else:
            return None, '', '', ''

    v_prev = docs[index + 1].version if index + 1 < len(docs) else ''
    v_next = docs[index - 1].version if index > 0 else ''

    status = 'old'
    if docs[index].date_apply > timezone.now():
        status = 'future'
    elif docs[0].date_apply >= timezone.now() and index <= 1:
        status = 'current'
    return docs[index], status, v_prev, v_next


# /main/
def main(request):
    current_time = timezone.now()
    services = Service.objects.filter(is_shown=True, icon__isnull=False)
    notice = Notice.objects.filter(valid_from__lte=current_time,
                                   valid_to__gt=current_time).first()

    return render(request, 'main.html', {
        'services': services,
        'notice': notice,
    })


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

    return render(request, 'terms.html', {
        'term': term,
        'status': status,
        'prev_v': prev_v,
        'next_v': next_v,
        'now': timezone.now(),
    })


# /privacy/{{version}}/
def privacy(request, version=''):
    privacy, status, prev_v, next_v = _get_document('PRIVACY', version)
    if not privacy:
        return redirect('/')

    return render(request, 'privacy.html', {
        'privacy': privacy,
        'status': status,
        'prev_v': prev_v,
        'next_v': next_v,
        'now': timezone.now()
    })


# /stats/
def stats(request):
    level = 0
    if request.user.is_authenticated:
        if request.user.is_staff:
            level = 2
        elif request.user.profile.sparcs_id:
            level = 1

    time = None
    raw_stat = {}
    raw_stats = Statistic.objects.order_by('-time')
    if len(raw_stats) > 0:
        time = raw_stats[0].time
        raw_stat = json.loads(raw_stats[0].data)

    stat = []
    for name, value in raw_stat.items():
        if name != 'all':
            service = Service.objects.filter(name=name).first()
            if not service or (level < 1 and not service.is_shown):
                continue

        s = {}
        s['name'] = name
        s['alias'] = service.alias if name != 'all' else 'all'
        s.update(value)

        if name == 'all':
            stat.insert(0, s)
        else:
            stat.append(s)

    return render(request, 'stats.html', {
        'level': level,
        'time': time,
        'stat': stat
    })


# /help/
def help(request):
    return render(request, 'help.html')


# /contact/
def contact(request):
    submitted = False
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        topic = request.POST.get('topic', '')
        title = request.POST.get('title', '')
        message = request.POST.get('message', '')
        result = validate_recaptcha(
            request.POST.get('g-recaptcha-response', '')
        )

        if name and email and topic and title and message and result:
            subject = f'[SPARCS SSO Report - {topic}] {title} (by {name})'
            send_mail(subject, message, email, settings.TEAM_EMAILS)
            submitted = True

    return render(request, 'contact.html', {'submitted': submitted})
