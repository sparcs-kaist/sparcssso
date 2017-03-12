from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from apps.core.models import UserLog
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Collect DB logs to a file'
    timestamp_file = '{}.last'.format(settings.LOG_FILE)

    def get_timestamp(self):
        try:
            with open(self.timestamp_file, 'r') as f:
                return float(f.read().strip())
        except:
            return 0.0

    def set_timestamp(self, timestamp):
        with open(self.timestamp_file, 'w') as f:
            f.write(str(timestamp))

    def handle(self, *args, **options):
        # remove logs that exceed 30 days
        last_month = (timezone.now() - timedelta(days=30)) \
            .replace(hour=0, minute=0, second=0, microsecond=0)
        UserLog.objects.filter(time__lt=last_month).delete()

        # cold archive logs from last backup time
        start_timestamp = self.get_timestamp()
        start_time = timezone.make_aware(
            datetime.fromtimestamp(start_timestamp))
        logs = UserLog.objects.filter(time__gt=start_time)

        end_time = start_time
        with open(settings.LOG_FILE, 'a') as f:
            for log in logs:
                end_time = max(end_time, log.time)
                f.write(log.pretty() + '\n')
        self.set_timestamp(end_time.timestamp())

        if settings.DEBUG:
            return

        # send critical logs to admin
        logs_critical = logs.filter(level__gte=30)
        content = map(lambda x: x.pretty() + '\n', logs_critical)
        emails = map(lambda x: x[1], settings.ADMINS)
        send_mail('[SPARCS SSO] Log Report', '', 'noreply@sso.sparcs.org',
                  emails, html_message=content)
