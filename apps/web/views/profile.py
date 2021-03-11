from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.backends import token_issue_email_auth, real_user_required
from apps.web.serializers.profile import UserViewSerializer, UserProfileEditSerializer


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserViewSerializer(request.user)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserProfileEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer.validated_data)
        pass


@api_view(['POST'])
@login_required
def email_send(request):
    # TODO: Edge cases
    user, profile = request.user, request.user.profile
    token_issue_email_auth(user)
    return Response({}, status=status.HTTP_200_OK)


@api_view(['GET'])
@login_required
@real_user_required
def email_verify(request, token_id):
    pass
