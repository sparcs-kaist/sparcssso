from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from apps.core.models import Statistic, Service
import json


class Command(BaseCommand):
    help = 'Get statistics of users'

    def handle(self, *args, **options):
        services = map(lambda x: x.name, Service.objects.all()) + ['all']
        stats = {}
        for service in services:
            stats[service] = {
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

        users = User.objects.all()
        for user in users:
            if user.profile.expire_time:
                continue

            services = ['all']
            for m in user.services.all():
                if m.unregister_time:
                    continue
                services.append(m.service.name)

            for service in services:
                stat = stats[service]
                stat['account']['all'] += 1
                if user.profile.email_authed:
                    stat['account']['email'] += 1
                if user.profile.facebook_id:
                    stat['account']['fb'] += 1
                if user.profile.twitter_id:
                    stat['account']['tw'] += 1
                if user.profile.kaist_id:
                    stat['account']['kaist'] += 1
                if user.profile.is_for_test:
                    stat['account']['test'] += 1

                if user.profile.gender == 'M':
                    stat['gender']['male'] += 1
                if user.profile.gender == 'F':
                    stat['gender']['female'] += 1
                if user.profile.gender == 'E':
                    stat['gender']['etc'] += 1

                if user.profile.birthday:
                    year = user.profile.birthday.year
                    if year in stat['birth_year']:
                        stat['birth_year'][year] += 1
                    else:
                        stat['birth_year'][year] = 1

                if not user.profile.kaist_info:
                    continue

                kaist_info = json.loads(user.profile.kaist_info)
                kaist = stat['kaist']

                if 'ku_std_no' in kaist_info:
                    start_year = kaist_info['ku_std_no'][:4]
                    if start_year in kaist['start_year']:
                        kaist['start_year'][start_year] += 1
                    else:
                        kaist['start_year'][start_year] = 1

                if 'ku_born_date' in kaist_info:
                    birth_year = kaist_info['ku_born_date'][:4]
                    if birth_year in kaist['birth_year']:
                        kaist['birth_year'][birth_year] += 1
                    else:
                        kaist['birth_year'][birth_year] = 1

                if 'ku_sex' in kaist_info:
                    gender = 'male' if kaist_info['ku_sex'] == 'M' else 'female'
                    kaist['gender'][gender] += 1

                if 'ku_kaist_org_id' in kaist_info:
                    department = kaist_info['ku_kaist_org_id']
                    if department in kaist['department']:
                        kaist['department'][department] += 1
                    else:
                        kaist['department'][department] = 1

                if 'employeeType' in kaist_info:
                    p_type = kaist_info['employeeType']
                    if 'E' in p_type:
                        kaist['employee'] += 1
                    elif 'P' in p_type:
                        kaist['professor'] += 1

        Statistic(time=timezone.now(), data=json.dumps(stats)).save()
