from django.utils import timezone
from apps.core.models import ServiceMap
from secrets import token_hex
import hmac
import time
import requests


# Register Service
def service_register(user, service):
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if m and not m.unregister_time:
        return False
    elif m and m.unregister_time and \
            (timezone.now() - m.unregister_time).days < service.cooltime:
        return False
    elif m:
        m.delete()

    while True:
        sid = token_hex(10)
        if not ServiceMap.objects.filter(sid=sid).count():
            break

    ServiceMap(sid=sid, user=user, service=service,
               register_time=timezone.now(), unregister_time=None).save()
    return True


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

    # TODO: code going crazy! should be refactored
    client_id = service.name
    sid = map_obj.sid
    timestamp = int(time.time())
    msg = ''.join([client_id, sid, str(timestamp)])
    sign = hmac.new(service.secret_key.encode(), msg.encode()).hexdigest()
    try:
        r = requests.post(service.unregister_url, data={
            'client_id': client_id,
            'sid': sid,
            'timestamp': timestamp,
            'sign': sign,
        })
        result = r.json()
    except:
        return unknown_error

    # TODO: code going crazy! should be refactored
    sid = result.get('sid', '')
    success = result.get('success', False)
    reason = result.get('reason', '')
    link = result.get('link', '')
    timestamp = result.get('timestamp', '')
    sign = result.get('sign', '')
    msg = ''.join(list(map(str, [sid, success, reason, link, timestamp])))
    sign_client = hmac.new(service.secret_key.encode(),
                           msg.encode()).hexdigest()
    if abs(time.time() - int(timestamp)) > 60:
        return unknown_error
    elif sid != map_obj.sid:
        return unknown_error
    elif not hmac.compare_digest(sign, sign_client):
        return unknown_error

    if result.get('success', False):
        map_obj.unregister_time = timezone.now()
        map_obj.save()
    return result
