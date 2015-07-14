from django.db import models
from django.contrib.auth.models import User


MALE = 'M'
FEMALE = 'F'
NONE = 'N'
GENDER = (
    (MALE, 'Male'),
    (FEMALE, 'Female'),
    (NONE, 'None'),
)


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
>>>>>>> b9b4fd3d759f26e3a0e77531e07b4f2a06ea1693
    user = models.OneToOneField(User, related_name='user_profile')
    gender = models.CharField(max_length=1, choices=GENDER, default=NONE)
    birthday = models.DateTimeField(blank=True, null=True)
    email_authed = models.BooleanField(default=False)
    email_auth_token = models.OneToOneField(EmailAuthToken,
                                            related_name='user_profile')
    facebook_id = models.CharField(max_length=50, blank=True, null=True)
    facebook_token = models.CharField(max_length=255, blank=True, null=True)


class SocialSignupInfo(models.Model):
    uid = models.CharField(max_length=64)
    userid = models.CharField(max_length=64)
    email = models.CharField(max_length=100)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=64)
    gender = models.CharField(max_length=1, choices=GENDER, default=NONE)
