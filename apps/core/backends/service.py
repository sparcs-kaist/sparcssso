import hmac
import time
from secrets import token_hex

import requests
from django.utils import timezone

from apps.core.models import ServiceMap


# Register Service
def service_register(user, service):
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if m and not m.unregister_time:
        return None
    elif m and m.unregister_time and \
            (timezone.now() - m.unregister_time).days < service.cooltime:
        return None
    elif m:
        m.delete()

    while True:
        sid = token_hex(10)
        if not ServiceMap.objects.filter(sid=sid).count():
            break

    m = ServiceMap(sid=sid, user=user, service=service,
                   register_time=timezone.now())
    m.save()
    return m


# Unregister Service
def service_unregister(map_obj):
    unknown_error = {
        'success': False,
        'reason': 'You cannot unregister this SPARCS service.',
    }

    if map_obj.unregister_time:
        return {'success': False}

    service = map_obj.service
    if not service.unregister_url:
        if service.scope == 'TEST':
            map_obj.unregister_time = timezone.now()
            map_obj.save()
            return {'success': True}
        elif service.scope == 'SPARCS':
            return unknown_error
        else:
            return unknown_error

    client_id = service.name
    sid = map_obj.sid
    timestamp = int(time.time())
    sign = hmac.new(
        service.secret_key.encode(),
        ''.join([sid, str(timestamp)]).encode(),
    ).hexdigest()
    try:
        r = requests.post(service.unregister_url, data={
            'client_id': client_id,
            'sid': sid,
            'timestamp': timestamp,
            'sign': sign,
        })
        result = r.json()
    except Exception:
        return unknown_error

    if result.get('success', False):
        map_obj.unregister_time = timezone.now()
        map_obj.save()
    return result
