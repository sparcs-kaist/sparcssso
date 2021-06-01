import os

if os.environ.get('SSO_LOCAL', '0') == '1':
    from dotenv import load_dotenv
    load_dotenv(override=True)
    if os.environ.get('SSO_ENV') != 'development':
        print('SSO_ENV must be development if SSO_LOCAL is true.')
        exit(1)

if os.environ.get('SSO_ENV') == "development":
    from .development import *  # noqa: F401, F403
else:
    from .production import *  # noqa: F401, F403
