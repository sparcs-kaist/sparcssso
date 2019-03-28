from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils import timezone, translation

from apps.core.backends import validate_recaptcha
from apps.core.models import Document, Notice, Service, Statistic


def _get_document(category, version=''):
    docs = Document.objects.filter(category=category).order_by('-date_apply')
    if not len(docs):
        return None, '', '', ''

    index_current = next(
        i for i, doc in enumerate(docs)
        if doc.date_apply <= timezone.now())
    index = index_current
    if version:
        index = next((i for i, doc in enumerate(docs)
                      if doc.version == version), None)
        if index is None:
            return None, '', '', ''

    v_prev = docs[index + 1].version if index + 1 < len(docs) else ''
    v_next = docs[index - 1].version if index > 0 else ''
    status = (
        'future' if index_current > index else
        'old' if index_current < index else 'current')
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
        'now': timezone.now(),
    })


# /stats/
def stats(request):
    level = 0
    if request.user.is_authenticated:
        if request.user.is_staff:
            level = 2
        elif request.user.profile.sparcs_id:
            level = 1

    stat = Statistic.objects.order_by('-time').first()
    time = stat.time if stat else None

    return render(request, 'stats.html', {
        'level': level,
        'time': time,
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
            request.POST.get('g-recaptcha-response', ''),
        )

        if name and email and topic and title and message and result:
            subject = f'[SPARCS SSO Report - {topic}] {title} (by {name})'
            send_mail(subject, message, email, settings.TEAM_EMAILS)
            submitted = True

    return render(request, 'contact.html', {
        'submitted': submitted,
        'captcha_enabled': 'y' if settings.RECAPTCHA_SECRET else '',
    })


# csrf failure view
def csrf_failure(request, reason=''):
    return render(request, 'error/csrf.html')
