from django.conf import settings


def version(request):
    prefix, version, simple_hash = settings.VERSION.split('-')
    return {
        'VERSION_CLASS': f'version-{prefix}',
        'VERSION_STRING': f'{version} ({simple_hash})',
    }
