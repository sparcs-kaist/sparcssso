from rest_framework import serializers

from apps.core.models import Notice


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ['title', 'text']
