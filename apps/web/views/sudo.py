from datetime import datetime
from typing import Optional

from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.backends import logging, sudo_password_needed
from apps.core.backends.sudo import sudo_password_expires_at, sudo_remove, sudo_renew
from apps.web.serializers.sudo import SudoRenewSerializer, SudoStatusSerializer


class SudoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        valid = False
        expires_at: Optional[datetime] = None

        if not request.user.has_usable_password():
            valid = True
        elif not sudo_password_needed(request.session):
            valid = True
            expires_at = sudo_password_expires_at(request.session)

        serializer = SudoStatusSerializer({
            "valid": valid,
            "expires_at": expires_at,
        })
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        if not request.user.has_usable_password():
            sudo_renew(request)
            return Response({}, status=status.HTTP_200_OK)

        sudo_remove(request)
        body = SudoRenewSerializer(data=request.data)
        body.is_valid(raise_exception=True)

        logger = logging.getLogger('sso.auth')
        password = body.validated_data.get("password")
        success = check_password(password, request.user.password)

        log_msg = 'success' if success else 'fail'
        (logger.info if success else logger.warning)(f'sudo.{log_msg}', {
            'r': request,
            'extra': [('path', request.path)],
        })
        if success:
            sudo_renew(request)
            return Response({}, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request):
        sudo_remove(request)
