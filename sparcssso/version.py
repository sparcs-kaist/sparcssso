import re
import subprocess
from datetime import datetime


def get_version_info():
    log_re = re.compile('^"([0-9a-f]{40}) ([^\(]+) \((.+)\)"$')
    try:
        out, err = subprocess.Popen(
            ['git', 'log', '-1', '--pretty="%H %ci%d"'],
            stdout=subprocess.PIPE,
        ).communicate()
        if err:
            raise RuntimeError()

        match_obj = log_re.match(out.decode().strip())
        git_hash = match_obj.group(1)[:8]
        time = datetime.strptime(
            match_obj.group(2),
            '%Y-%m-%d %H:%M:%S %z',
        )
        branch = match_obj.group(3)
    except:
        return 'unknown-00000000T000000-00000000'

    if 'master' in branch:
        prefix = 'release'
    elif 'develop' in branch:
        prefix = 'beta'
    else:
        prefix = 'nightly'
    simple_time = time.strftime('%Y%m%dT%H%m%S')
    return f'{prefix}-{simple_time}-{git_hash}'
