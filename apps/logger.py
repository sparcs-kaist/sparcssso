from logging.handlers import RotatingFileHandler


class FileHandler(RotatingFileHandler, object):
    def emit(self, record):
        if len(record.args) > 0:
            request = record.args[0]
            record.ip = request.META.get('REMOTE_ADDR', '0.0.0.0')

            record.username = 'undefined'
            if request.user.is_authenticated():
                record.username = request.user.username
            record.args = None
        else:
            record.ip = '127.0.0.1'
            record.username = 'system'

        super(FileHandler, self).emit(record)
