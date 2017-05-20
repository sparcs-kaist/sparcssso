from django.conf import settings


def version(request):
    prefix, version = settings.VERSION.split('-')
    return {
        'VERSION_CLASS': f'version-{prefix}',
        'VERSION_STRING': version,
    }
