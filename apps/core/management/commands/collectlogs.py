from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from apps.core.models import UserLog
from datetime import timedelta


class Command(BaseCommand):
    help = 'Collect one day log to file'

    def handle(self, *args, **options):
        yesterday = (timezone.now() - timedelta(days=1)) \
                    .replace(hour=0, minute=0, second=0, microsecond=0)
        last_month = (timezone.now() - timedelta(days=30)) \
                    .replace(hour=0, minute=0, second=0, microsecond=0)
        UserLog.objects.filter(time__lt=last_month).delete()
        logs = UserLog.objects.filter(time__gte=yesterday)
        with open(settings.LOG_FILE, 'a') as f:
            for log in logs:
                f.write(log.pretty() + '\n')

        if settings.DEBUG:
            return

        logs_critical = logs.filter(level__gte=30)
        content = map(lambda x: x.pretty() + '\n', logs_critical)
        emails = map(lambda x: x[1], settings.ADMINS)
        send_mail('[SPARCS SSO] Log Report', '', 'noreply@sso.sparcs.org',
                  emails, html_message=content)
