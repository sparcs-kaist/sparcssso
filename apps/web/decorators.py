from functools import wraps

from rest_framework import status
from rest_framework.response import Response

from apps.core.backends import sudo_password_needed, sudo_renew


def api_sudo_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.has_usable_password():
            return view_func(request, *args, **kwargs)
        if not sudo_password_needed(request.session):
            sudo_renew(request)
            return view_func(request, *args, **kwargs)
        return Response({}, status=status.HTTP_412_PRECONDITION_FAILED)
    return _wrapped_view
