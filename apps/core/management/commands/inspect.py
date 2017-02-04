from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
import netaddr
import os


class Command(BaseCommand):
    help = 'Inspect a user'

    def add_arguments(self, parser):
        parser.add_argument('--uid', dest='uid', help='uid to inspect')
        parser.add_argument('--sid', dest='sid', help='sid to inspect')
        parser.add_argument('--email', dest='email', help='email to inspect')
        parser.add_argument('--ip', dest='ip', help='ip to inspect')

    def handle(self, *args, **options):
        print('=====SPARCS SSO USER INSPECTION TOOL=====')
        print('OPTIONS: uid={}, sid={}, email={}, ip={}'.format(
            options['uid'], options['sid'], options['email'], options['ip']))
        print()

        if options['ip']:
            ip = options['ip']
            print('> INSPECT LOG WHERE IP=%s' % ip)

            if not netaddr.valid_ipv4(ip, netaddr.INET_PTON):
                print('>> INVAILD IP')
                return

            target = '({})'.format(ip)
        elif options['uid'] or options['sid'] or options['email']:
            if options['uid']:
                print('> FIND USER WHERE uid=%s' % options['uid'])
                users = User.objects.filter(username__contains=options['uid'])
            elif options['sid']:
                print('> FIND USER WHERE sid=%s' % options['sid'])
                users = User.objects.filter(services__sid__contains=options['sid'])
            elif options['email']:
                print('> FIND USER WHERE email=%s' % options['email'])
                users = User.objects.filter(email__contains=options['email'])

            if len(users) > 100:
                print('>> TOO MANY USER')
                return
            elif not users:
                print('>> NO USER')
                return

            for user in users:
                print('>> USER: uid={}, first_name={}, last_name={}, email={}'.format(
                    user.username, user.first_name, user.last_name, user.email))

            if len(users) != 1:
                return

            user = users[0]
            print('> INSPECT LOG EXACT uid=%s' % user.username)
            target = user.username + ')'
        else:
            print('> NO TARGET SPECIFIED')
            return

        log_base = settings.LOGGING['handlers']['file']['filename']
        log_ext = ['5', '4', '3', '2', '1', '']
        for ext in log_ext:
            log_name = log_base + ext
            if not os.path.isfile(log_name):
                continue

            with open(log_name, 'r') as f:
                for line in f:
                    if target in line:
                        print(line.strip())
