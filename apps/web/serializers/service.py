from rest_framework import serializers

from apps.core.models import Service


class ServiceThumbSerializer(serializers.ModelSerializer):
    """
    Serializer for service list item, intended to be viewed to public users
    """
    class Meta:
        model = Service
        fields = ['main_url', 'icon_url', 'name', 'alias']
