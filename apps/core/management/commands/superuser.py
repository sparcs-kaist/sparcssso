from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.core.models import UserProfile


class Command(BaseCommand):
    help = 'Make initial superuser'

    def handle(self, *args, **options):
        if User.objects.all().count() > 0:
            self.stdout.write('Only use at first setup')
            return

        user = User.objects.create_user(username='sysop',
                                        first_name='sysop',
                                        last_name='',
                                        email='admin@sso.sparcs.org',
                                        password='adminadmin')
        user.is_staff = True
        user.is_superuser = True
        user.save()

        user.profile = UserProfile(user=user, email_authed=True)
        user.profile.save()

        print('Superuser created with admin@sso.sparcs.org / adminadmin')
