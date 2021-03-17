from rest_framework import serializers, fields

from apps.core.models import Notice


class NoticeFilterSerializer(serializers.Serializer):
    offset = fields.IntegerField(required=False, default=0, min_value=0)
    limit = fields.IntegerField(required=False, default=3, min_value=0, max_value=10)
    date_after = fields.IntegerField(required=False, default=0, min_value=0)


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ['valid_from', 'valid_to', 'title', 'text']
