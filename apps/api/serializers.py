from rest_framework import fields, serializers

from apps.core.models import Notice


class NoticeFilterSerializer(serializers.Serializer):
    offset = fields.IntegerField(required=False, default=0, min_value=0)
    limit = fields.IntegerField(required=False, default=3, min_value=0, max_value=10)
    date_after = fields.IntegerField(required=False, default=0, min_value=0)


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ['valid_from', 'valid_to', 'title', 'text']


class TokenInfoQuerySerializer(serializers.Serializer):
    client_id = serializers.CharField(required=True)
    timestamp = serializers.CharField(required=True)
    sign = serializers.CharField(required=True)
    code = serializers.CharField(required=True)
