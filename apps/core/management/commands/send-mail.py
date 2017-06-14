from datetime import datetime
from os import path

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import UserLog


class Command(BaseCommand):
    help = 'Send warning logs to the admin email'
    timestamp_file = path.join(settings.LOG_DIR, 'warning.stamp')

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
        start_time = timezone.make_aware(
            datetime.fromtimestamp(self.get_timestamp()),
        )
        logs = UserLog.objects.filter(
            time__gt=start_time, level__gte=30,
        ).all()
        if not logs:
            return

        end_time = max(list(map(lambda x: x.time, logs)))
        self.set_timestamp(end_time.timestamp())

        if settings.DEBUG:
            return

        content = ''.join(list(map(lambda x: x.pretty() + '<br/>\n', logs)))
        emails = list(map(lambda x: x[1], settings.ADMINS))
        send_mail('[SPARCS SSO] Log Report', '', 'noreply@sso.sparcs.org',
                  emails, html_message=content)
