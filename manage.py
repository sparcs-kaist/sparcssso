#!/usr/bin/env python
import os
import sys


if os.environ.get('SSO_LOCAL', '0') == '1':
    from dotenv import load_dotenv
    load_dotenv(override=True)
    if os.environ.get('SSO_ENV') != 'development':
        print('SSO_ENV must be development if SSO_LOCAL is true.')
        exit(1)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sparcssso.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
