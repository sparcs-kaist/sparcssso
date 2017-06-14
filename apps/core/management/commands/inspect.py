import os
import re

import netaddr
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone


TOOL_VERSION = 'v1.0'
BANNER = '\n'.join([
    '=================== SPARCS SSO Log Inspection Report ===================',
    '              >> CONFIDENTIAL - Authorized Person Only <<               ',
    'This report contains personal information. This report may be read only ',
    'by SPARCS SSO system operators, and the person who reasonably needs to  ',
    'within law enforcement agencies. It is strictly forbidden that copying  ',
    'disclosing or sharing this report with others, unless permitted to do   ',
    'so by SPARCS SSO system operators, or by existing laws.                 ',
    '------------------------------------------------------------------------',
])


class Command(BaseCommand):
    help = 'Inspect a user'

    def add_arguments(self, parser):
        parser.add_argument('--uid', dest='uid', help='user unique id')
        parser.add_argument('--sid', dest='sid', help='service map id')
        parser.add_argument('--email', dest='email', help='email address')
        parser.add_argument('--ip', dest='ip', help='valid ipv4 address')
        parser.add_argument('--limit', dest='limit', help='fetch limit')

    def check_options(self, options):
        count, target_prop = 0, ''
        for prop in ['uid', 'sid', 'email', 'ip']:
            if options[prop]:
                count += 1
                target_prop = prop

        if count > 1:
            self.stdout.write('* Query: invalid (two or more target)')
            return
        elif count == 0:
            self.stdout.write('* Query: no item specified')
            return

        target_val = options[target_prop]
        self.stdout.write(f'* Query: {target_prop}={target_val}')
        if target_prop == 'ip':
            if not netaddr.valid_ipv4(target_val, netaddr.INET_PTON):
                self.stdout.write('  - Invalid IP')
                self.stdout.write('=' * 72)
                return
            return f'({target_val}'

        if options['uid']:
            users = User.objects.filter(
                username__contains=options['uid'],
            )
        elif options['sid']:
            users = User.objects.filter(
                services__sid__contains=options['sid'],
            )
        elif options['email']:
            users = User.objects.filter(
                email__contains=options['email'],
            )

        if len(users) > 100:
            self.stdout.write('  - Too Many Users')
            return
        elif not users:
            self.stdout.write('  - No Such User')
            return

        for user in users:
            self.stdout.write(''.join([
                f'  - User: {user.username}, {user.first_name}',
                f'/{user.last_name} ,{user.email}',
            ]))

        if len(users) != 1:
            return
        return f'{users[0].username})'

    def search_logs(self, log_files, search_str, limit):
        logs, logs_count = [], 0
        for log_file in log_files:
            part_logs = []
            with open(log_file, 'r') as f:
                for log in f.readlines():
                    if logs_count > limit:
                        break
                    elif search_str in log:
                        part_logs.append(log)
                        logs_count += 1
            logs = part_logs + logs
        return logs, logs_count

    def print_logs(self, search_str, limit):
        try:
            limit = int(limit)
        except:
            limit = 500

        log_buffer_files = list(map(
            lambda x: os.path.join(settings.LOG_BUFFER_DIR, x),
            filter(
                lambda x: re.match(r'\d{8}\.\d+\.log', x),
                os.listdir(settings.LOG_BUFFER_DIR),
            ),
        ))
        logs_buffer, logs_buffer_count = self.search_logs(
            log_buffer_files, search_str, limit,
        )
        logs_buffer.sort()

        log_files = reversed(sorted(list(map(
            lambda x: os.path.join(settings.LOG_DIR, x),
            filter(
                lambda x: re.match(r'\d{8}\.log', x),
                os.listdir(settings.LOG_DIR),
            ),
        ))))
        logs, logs_count = self.search_logs(
            log_files, search_str, limit - logs_buffer_count,
        )

        for log in logs:
            self.stdout.write(log)
        for log in logs_buffer:
            self.stdout.write(log)

    def handle(self, *args, **options):
        self.stdout.write(BANNER)
        self.stdout.write('\n'.join([
            f'* SSO Version: {settings.VERSION}',
            f'* Inspection Tool Version: {TOOL_VERSION}',
            f'* Time: {timezone.now().isoformat()}',
            '-' * 72,
        ]))
        search_str = self.check_options(options)
        self.stdout.write('=' * 72)
        self.stdout.write('')

        if search_str:
            self.print_logs(search_str, options['limit'])
