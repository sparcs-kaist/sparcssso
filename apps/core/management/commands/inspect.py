from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
import netaddr


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
            print(f'> INSPECT LOG WHERE IP={ip}')

            if not netaddr.valid_ipv4(ip, netaddr.INET_PTON):
                print('>> INVAILD IP')
                return

            target = f'({ip}'
        elif options['uid'] or options['sid'] or options['email']:
            if options['uid']:
                print(f'> FIND USER WHERE uid={options["uid"]}')
                users = User.objects.filter(
                    username__contains=options['uid']
                )
            elif options['sid']:
                print(f'> FIND USER WHERE sid={options["sid"]}')
                users = User.objects.filter(
                    services__sid__contains=options['sid']
                )
            elif options['email']:
                print(f'> FIND USER WHERE email={options["email"]}')
                users = User.objects.filter(
                    email__contains=options['email']
                )

            if len(users) > 100:
                print('>> TOO MANY USER')
                return
            elif not users:
                print('>> NO USER')
                return

            for user in users:
                print(
                    f'>> USER: uid={user.username}, ' +
                    f'first_name={user.first_name}, ' +
                    f'last_name={user.last_name}, ' +
                    f'email={user.email}'
                )

            if len(users) != 1:
                return

            user = users[0]
            print(f'> INSPECT LOG EXACT uid={user.username}')
            target = user.username + ')'
        else:
            print('> NO TARGET SPECIFIED')
            return

        with open(settings.LOG_FILE, 'r') as f:
            for line in f:
                if target in line:
                    print(line.strip())
