import os
import re
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import UserLog


class Command(BaseCommand):
    help = 'Merge log files into one file'

    def get_full_path(self, log_file):
        return os.path.join(settings.LOG_BUFFER_DIR, log_file)

    def handle(self, *args, **options):
        # merge multiple log files into one file
        log_files = list(filter(
            lambda x: re.match(r'(\d{8})\.(\d+)\.log', x),
            os.listdir(settings.LOG_BUFFER_DIR),
        ))
        log_entities = {}
        for log_file in log_files:
            date = log_file[:8]
            if date not in log_entities:
                log_entities[date] = []

            with open(self.get_full_path(log_file), 'r') as f:
                log_entities[date].extend(
                    list(filter(None, f.readlines())),
                )

        for date, log_entity in log_entities.items():
            log_entity.sort()
            log_file = os.path.join(settings.LOG_DIR, f'{date}.log')
            with open(log_file, 'a+') as f:
                for log in log_entity:
                    f.write(log)

        for log_file in log_files:
            os.remove(self.get_full_path(log_file))

        # remove logs that exceed 30 days
        last_month = (timezone.now() - timedelta(days=30)) \
            .replace(hour=0, minute=0, second=0, microsecond=0)
        UserLog.objects.filter(time__lt=last_month).delete()
