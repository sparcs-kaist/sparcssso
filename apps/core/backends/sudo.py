import time

from django.contrib.sessions.backends.base import SessionBase

SUDO_TIMEOUT_SEC = 600
SUDO_SESSION_KEY = 'sudo_timestamp'


def sudo_password_needed(session: SessionBase) -> bool:
    """
    Check whether password reentry is necessary for sudo actions
    """
    timestamp = int(session.get(SUDO_SESSION_KEY, '0'))
    return time.time() - timestamp < SUDO_TIMEOUT_SEC


def sudo_renew(session: SessionBase) -> None:
    """
    Renew sudo session timeout
    """
    session[SUDO_SESSION_KEY] = time.time()
