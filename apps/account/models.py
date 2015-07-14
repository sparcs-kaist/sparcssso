from django.db import models
from django.contrib.auth.models import User


class EmailAuthToken(models.Model):
    token = models.CharField(max_length=48, primary_key=True)
    expire_time = models.DateTimeField()


class UserProfile(models.Model):
    MALE = 'M'
    FEMALE = 'F'
    NONE = 'N'
    GENDER = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
        (NONE, 'None'),
    )
    user = models.OneToOneField(User, related_name='user_profile')
    gender = models.CharField(max_length=1, choices=GENDER, default=NONE)
    birthday = models.DateTimeField(blank=True, null=True)
    email_authed = models.BooleanField(default=False)
    email_auth_token = models.OneToOneField(EmailAuthToken,
                                            related_name='user_profile')
    facebook_id = models.CharField(max_length=50, blank=True, null=True)
    facebook_token = models.CharField(max_length=255, blank=True, null=True)
