import os


if os.environ.get('SSO_ENV') == "development":
    from .development import *  # noqa: F401, F403
else:
    from .production import *  # noqa: F401, F403
