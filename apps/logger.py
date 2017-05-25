from django.apps import apps
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import localtime
from logging import Handler
from os import path
import os


class SSOLogHandler(Handler):
    initialized = False
    log_file = None
    log_name = None

    def initialize(self):
        self.User = apps.get_model('auth', 'User')
        self.UserLog = apps.get_model('core', 'UserLog')

    def get_log_name(self):
        pid, date = os.getpid(), localtime(timezone.now()).strftime('%Y%m%d')
        return f'{date}.{pid}.log'

    def emit_file(self, data):
        log_name = self.get_log_name()
        if self.log_name != log_name:
            if self.log_file:
                self.log_file.close()
            self.log_name = log_name
            self.log_file = open(path.join(
                settings.LOG_BUFFER_DIR, self.log_name
            ), 'a+')

        time = localtime(timezone.now()).isoformat()
        if data['user']:
            username = data['user'].username
        else:
            username = data['username']
        level, ip, text = data['level'], data['ip'], data['text']
        self.log_file.write(f'{time}/{level} ({ip}, {username}) {text}\n')
        self.log_file.flush()

    def emit_db(self, data):
        if data['user']:
            user = data['user']
        else:
            user = self.User.objects.filter(username=data['username']).first()

        self.UserLog(
            user=user, level=data['level'], ip=data['ip'],
            text=data['text'], hide=data['hide'],
        ).save()

    def emit(self, record):
        if not self.initialized:
            self.initialize()

        data = {
            'user': None,
            'username': record.args.get('uid', 'undefined'),
            'level': record.levelno,
            'text': f'{record.name}.{record.getMessage()}',
            'hide': record.args.get('hide', False),
        }
        request = record.args.get('r', None)
        if request:
            data['ip'] = request.META.get('REMOTE_ADDR', '0.0.0.0')
            if request.user.is_authenticated:
                data['user'] = request.user

        self.emit_file(data)
        self.emit_db(data)
