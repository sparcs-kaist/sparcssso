from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from apps.core.models import Statistic, Service
from datetime import timedelta
import json


class Command(BaseCommand):
    help = 'Get statistics of users'

    def build_template(self, services):
        self.stats = {}
        for service in services:
            self.stats[service] = {
                'account': {
                    'all': 0,
                    'email': 0,
                    'fb': 0,
                    'tw': 0,
                    'kaist': 0,
                    'test': 0,
                },
                'gender': {
                    'male': 0,
                    'female': 0,
                    'hide': 0,
                    'etc': 0,
                },
                'birth_year': {},
                'kaist': {
                    'start_year': {},
                    'birth_year': {},
                    'gender': {
                        'male': 0,
                        'female': 0,
                    },
                    'department': {},
                    'employee': 0,
                    'professor': 0,
                }
            }

    def add_basic_stat(self, service, user):
        stat = self.stats[service]
        stat['account']['all'] += 1
        if user.profile.email_authed:
            stat['account']['email'] += 1
        if user.profile.facebook_id:
            stat['account']['fb'] += 1
        if user.profile.twitter_id:
            stat['account']['tw'] += 1
        if user.profile.kaist_id:
            stat['account']['kaist'] += 1
        if user.profile.test_enabled:
            stat['account']['test'] += 1

        if user.profile.gender == '*M':
            stat['gender']['male'] += 1
        elif user.profile.gender == '*F':
            stat['gender']['female'] += 1
        elif user.profile.gender == '*H':
            stat['gender']['hide'] += 1
        else:
            stat['gender']['etc'] += 1

        if user.profile.birthday:
            year = user.profile.birthday.year
            if year in stat['birth_year']:
                stat['birth_year'][year] += 1
            else:
                stat['birth_year'][year] = 1

    def add_kaist_stat(self, service, kaist_info):
        kaist_stat = self.stats[service]['kaist']

        if 'ku_std_no' in kaist_info and \
                len(kaist_info['ku_std_no']) == 8:
            start_year = kaist_info['ku_std_no'][:4]
            if start_year in kaist_stat['start_year']:
                kaist_stat['start_year'][start_year] += 1
            else:
                kaist_stat['start_year'][start_year] = 1

        if 'ku_born_date' in kaist_info:
            birth_year = kaist_info['ku_born_date'][:4]
            if birth_year in kaist_stat['birth_year']:
                kaist_stat['birth_year'][birth_year] += 1
            else:
                kaist_stat['birth_year'][birth_year] = 1

        if 'ku_sex' in kaist_info:
            gender = 'male' if kaist_info['ku_sex'] == 'M' else 'female'
            kaist_stat['gender'][gender] += 1

        if 'ku_kaist_org_id' in kaist_info:
            department = kaist_info['ku_kaist_org_id']
            if department in kaist_stat['department']:
                kaist_stat['department'][department] += 1
            else:
                kaist_stat['department'][department] = 1

        if 'employeeType' in kaist_info:
            p_type = kaist_info['employeeType']
            if 'E' in p_type:
                kaist_stat['employee'] += 1
            elif 'P' in p_type:
                kaist_stat['professor'] += 1

    def handle(self, *args, **options):
        # get logs that over two month ago
        two_month = (timezone.now() - timedelta(days=60)) \
            .replace(hour=0, minute=0, second=0, microsecond=0)
        old_stats = Statistic.objects.filter(time__lt=two_month)
        with open(settings.STAT_FILE, 'a') as f:
            for old_stat in old_stats:
                f.write(old_stat.pretty() + '\n')
        old_stats.delete()

        # collect statistics of all services and all users
        services = list(map(lambda x: x.name,
                            Service.objects.all())) + ['all']
        users = User.objects.exclude(profile__expire_time__isnull=False) \
                            .exclude(profile__test_only=True)

        self.build_template(services)
        for user in users:
            services = list(map(lambda x: x.service.name,
                                filter(lambda x: not x.unregister_time,
                                       user.services.all()))) + ['all']
            for service in services:
                self.add_basic_stat(service, user)
                if user.profile.kaist_info:
                    kaist_info = json.loads(user.profile.kaist_info)
                    self.add_kaist_stat(service, kaist_info)

        Statistic(time=timezone.now(), data=json.dumps(self.stats)).save()
