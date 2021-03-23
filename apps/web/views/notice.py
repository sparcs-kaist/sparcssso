from django.utils import timezone
from rest_framework import decorators, viewsets
from rest_framework.response import Response

from apps.core.models import Notice
from apps.web.serializers.notice import NoticeSerializer


class NoticeViewSet(viewsets.ViewSet):
    queryset = Notice.objects
    serializer_class = NoticeSerializer

    def list(self, request):
        current_time = timezone.now()
        notices = self.queryset.queryset.filter(
            valid_from__lte=current_time,
            valid_to__gt=current_time,
        ).order_by('-valid_from')
        serializer = self.serializer_class(notices, many=True)
        return Response(serializer.data)

    @decorators.action(methods=['GET'], detail=False)
    def latest(self, request):
        current_time = timezone.now()
        notices = self.queryset.filter(
            valid_from__lte=current_time,
            valid_to__gt=current_time,
        ).order_by('-valid_from').first()
        serializer = self.serializer_class([notices], many=True)
        return Response(serializer.data)
