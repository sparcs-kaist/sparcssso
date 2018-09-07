import re
import subprocess
from datetime import datetime


def get_version_info(debug, allowed_hosts):
    log_re = re.compile('^([\da-f]{40}) ([^\(]+) .+$')
    try:
        proc = subprocess.run(
            'git log -1 --pretty="%H %ci%d"',
            stdout=subprocess.PIPE, shell=True)
        match_obj = log_re.match(proc.stdout.decode().strip())
        git_hash = match_obj.group(1)[:8]
        time = datetime.strptime(
            match_obj.group(2),
            '%Y-%m-%d %H:%M:%S %z',
        )
        proc = subprocess.run(
            'git status --porcelain',
            stdout=subprocess.PIPE, shell=True)
        dirty = bool(proc.stdout.decode().strip())
    except Exception:
        return 'unknown-00000000T000000-00000000'

    if 'sso.sparcs.org' in allowed_hosts:
        prefix = 'release'
    elif 'ssobeta.sparcs.org' in allowed_hosts:
        prefix = 'beta'
    else:
        prefix = 'dev'
    simple_time = time.strftime('%Y%m%dT%H%m%S')
    return f'{prefix}-{simple_time}-{git_hash}{":dirty" if dirty else ""}'
