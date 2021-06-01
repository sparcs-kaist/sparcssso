from rest_framework import serializers


class SudoStatusSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    expires_at = serializers.DateTimeField(default=None)


class SudoRenewSerializer(serializers.Serializer):
    password = serializers.CharField(required=True)
