from logging.handlers import RotatingFileHandler


class FileHandler(RotatingFileHandler, object):
    def emit(self, record):
        record.ip = '127.0.0.1'
        record.username = 'undefined'

        request = record.args.get('r', None)
        if request:
            record.ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            if request.user.is_authenticated():
                record.username = request.user.username

        if record.args.has_key('uid'):
            record.username = record.args['uid']

        super(FileHandler, self).emit(record)
