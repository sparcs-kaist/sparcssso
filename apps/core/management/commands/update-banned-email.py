import requests
from django.core.management.base import BaseCommand, CommandError

from apps.core.models import EmailDomain


DATA_URL = (
    'https://raw.githubusercontent.com/martenson/disposable-email-domains'
    '/master/disposable_email_blacklist.conf'
)


class Command(BaseCommand):
    help = 'Update list of banned email domains'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            dest='overwrite',
            help='Overwrite configured data',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            dest='clean',
            help='Empty the table and start from the beginning',
        )

    def handle(self, *args, **options):
        try:
            domains_raw = requests.get(DATA_URL).text.split('\n')
            domains = [x for x in [y.strip() for y in domains_raw] if x]
        except Exception:
            raise CommandError(f'cannot fetch data from {DATA_URL}')

        if options['clean']:
            EmailDomain.objects.all().delete()

        count_created, count_overwrited = 0, 0
        for domain in domains:
            obj, created = EmailDomain.objects.get_or_create(domain=domain)
            if created:
                count_created += 1
            elif not obj.is_banned and options['overwrite']:
                count_overwrited += 1
                obj.is_banned = True
                obj.save()

        self.stdout.write(self.style.SUCCESS(
            f'total {len(domains)}, '
            f'created {count_created}, '
            f'overwrited {count_overwrited}'))
