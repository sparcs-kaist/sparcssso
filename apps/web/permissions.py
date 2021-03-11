from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission

from apps.core.backends import sudo_password_needed, sudo_renew


class IsDeveloper(BasePermission):
    """
    Permission checking whether the user has developer permissions
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.flags.get('dev', False)


class IsAnonymous(BasePermission):
    """
    Permission checking whether the user is anonymous (ie. not authenticated)
    """
    def has_permission(self, request, view):
        return not request.user.is_authenticated


class IsRealUser(BasePermission):
    """
    Permission checking whether the user is a real user (ie. not a test account)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and not request.user.profile.test_only


class SudoRequiredAPIException(APIException):
    """
    Raises a HTTP 412 (Precondition Failed) response, indicating that password re-entry is necessary for this action
    """
    status_code = status.HTTP_412_PRECONDITION_FAILED
    default_code = 'error'

    def __init__(self, detail=None):
        if detail is None:
            # TODO: i18n
            detail = 'Please re-enter your password.'
        self.detail = detail


class IsSudoValid(BasePermission):
    def has_permission(self, request, view):
        if sudo_password_needed(request.session):
            raise SudoRequiredAPIException()
        sudo_renew(request.session)
        return True
