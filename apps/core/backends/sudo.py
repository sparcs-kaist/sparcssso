import datetime
import time

from django.contrib.sessions.backends.base import SessionBase
from django.utils import timezone

SUDO_TIMEOUT_SEC = 600
SUDO_SESSION_KEY = 'sudo_timestamp'


def sudo_password_needed(session: SessionBase) -> bool:
    """
    Check whether password reentry is necessary for sudo actions
    """
    timestamp = int(session.get(SUDO_SESSION_KEY, '0'))
    time_diff = time.time() - timestamp
    return time_diff >= SUDO_TIMEOUT_SEC or time_diff < 0


def sudo_password_expires_at(session: SessionBase) -> datetime.datetime:
    """
    Return exact expiry time of current sudo session
    """
    timestamp = int(session.get(SUDO_SESSION_KEY, '0'))
    renew_time = datetime.datetime.fromtimestamp(timestamp, timezone.get_default_timezone())
    renew_time += datetime.timedelta(seconds=SUDO_TIMEOUT_SEC)
    return renew_time


def sudo_renew(request) -> None:
    """
    Renew sudo session timeout
    """
    request.session[SUDO_SESSION_KEY] = time.time()


def sudo_remove(request) -> None:
    """
    Remove sudo session
    """
    if SUDO_SESSION_KEY in request.session:
        del request.session[SUDO_SESSION_KEY]
