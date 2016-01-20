from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.models import UserProfile
import logging


logger = logging.getLogger('sso.core.account')


class Command(BaseCommand):
    help = 'Remove expired users'

    def handle(self, *args, **options):
        profiles = UserProfile.objects.filter(expire_time__isnull=False,\
            expire_time__lte=timezone.now())

        for profile in profiles:
            username = profile.user.username
            profile.user.delete()

            logger.info('delete', {'uid': username})

