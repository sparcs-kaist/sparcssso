from django.contrib.auth.models import User
from rest_framework import serializers

from apps.core.models import UserProfile


class ProfileViewSerializer(serializers.ModelSerializer):
    facebook_connected = serializers.SerializerMethodField(read_only=True)
    twitter_connected = serializers.SerializerMethodField(read_only=True)
    test_only = serializers.BooleanField(read_only=True)
    test_enabled = serializers.BooleanField(read_only=True)

    def get_facebook_connected(self, obj: UserProfile) -> bool:
        return obj.facebook_id is not None

    def get_twitter_connected(self, obj: UserProfile) -> bool:
        return obj.twitter_id is not None

    class Meta:
        model = UserProfile
        fields = ['gender', 'birthday', 'test_only', 'test_enabled', 'facebook_connected', 'twitter_connected']


class UserViewSerializer(serializers.ModelSerializer):
    profile = ProfileViewSerializer()
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'profile', 'first_name', 'last_name']


class ProfileEditSerializer(serializers.ModelSerializer):
    gender = serializers.CharField(required=True, max_length=30)
    birthday = serializers.DateField(required=False)

    class Meta:
        model = UserProfile
        fields = ['gender', 'birthday']


class UserProfileEditSerializer(serializers.ModelSerializer):
    profile = ProfileViewSerializer(required=True)
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=150)

    class Meta:
        model = User
        fields = ['profile', 'first_name', 'last_name']
