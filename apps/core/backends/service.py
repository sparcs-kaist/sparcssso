from django.utils import timezone
from apps.core.models import ServiceMap
from secrets import token_hex


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
def service_unregister(user, service):
    m = ServiceMap.objects.filter(user=user, service=service).first()
    if not m or m.unregister_time:
        return False

    m.unregister_time = timezone.now()
    m.save()
    return True
