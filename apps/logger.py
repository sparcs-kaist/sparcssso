from django.contrib.auth.models import User
from django.core.validators import ip_address_validators
from apps.core.models import UserLog
from logging.handlers import RotatingFileHandler


class FileHandler(RotatingFileHandler, object):
    def emit(self, record):
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

        if record.args.has_key('uid'):
            record.username = record.args['uid']

        hide = record.args.has_key('hide')
        user = User.objects.filter(username=record.username).first()
        if user and not hide:
            manager = user.user_logs
            if manager.count() >= 30:
                manager.order_by('time')[0].delete()
            UserLog(user=user, level=record.levelno, ip=record.ip,
                    text='%s.%s' % (record.name, record.getMessage())).save()

        super(FileHandler, self).emit(record)
