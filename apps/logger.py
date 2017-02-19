from django.core.validators import ip_address_validators
from django.apps import apps
from logging import Handler


class DBHandler(Handler):
    model_loaded = False

    def emit(self, record):
        if not self.model_loaded:
            self.User = apps.get_model('auth', 'User')
            self.UserLog = apps.get_model('core', 'UserLog')
            self.model_loaded = True

        record.ip = '0.0.0.0'
        record.username = 'undefined'

        request = record.args.get('r', None)
        if request:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            try:
                ip_address_validators('both', ip)
            except:
                ip = '0.0.0.0'
            record.ip = ip

            if request.user.is_authenticated():
                record.username = request.user.username

        if 'uid' in record.args:
            record.username = record.args['uid']

        hide = record.args.get('hide', False)
        user = self.User.objects.filter(username=record.username).first()
        self.UserLog(user=user, level=record.levelno, ip=record.ip, hide=hide,
                     text='%s.%s' % (record.name, record.getMessage())).save()
