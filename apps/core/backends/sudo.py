import time

from django.contrib.sessions.backends.base import SessionBase

SUDO_TIMEOUT_SEC = 600
SUDO_SESSION_KEY = 'sudo_timestamp'


def sudo_password_needed(session: SessionBase) -> bool:
    """
    Check whether password reentry is necessary for sudo actions
    """
    timestamp = int(session.get(SUDO_SESSION_KEY, '0'))
    time_diff = time.time() - timestamp
    return time_diff >= SUDO_TIMEOUT_SEC or time_diff < 0


def sudo_renew(request) -> None:
    """
    Renew sudo session timeout
    """
    request.session[SUDO_SESSION_KEY] = time.time()
