from django.db import models
from django.contrib.auth.models import User


MALE = 'M'
FEMALE = 'F'
ETC = 'E'
GENDER = (
    (MALE, 'Male'),
    (FEMALE, 'Female'),
    (ETC, 'etc'),
)


class EmailAuthToken(models.Model):
    token = models.CharField(max_length=48, primary_key=True)
    expire_time = models.DateTimeField()
    user_profile = models.ForeignKey('UserProfile')


class ResetPWToken(models.Model):
    token = models.CharField(max_length=48, primary_key=True)
    expire_time = models.DateTimeField()
    user_profile = models.ForeignKey('UserProfile')


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='user_profile')
    gender = models.CharField(max_length=1, choices=GENDER, default=ETC)
    birthday = models.DateTimeField(blank=True, null=True)
    email_authed = models.BooleanField(default=False)
    facebook_id = models.CharField(max_length=50, blank=True, null=True)
    twitter_id = models.CharField(max_length=50, blank=True, null=True)
    kaist_id = models.CharField(max_length=50, blank=True, null=True)


class SocialSignupInfo(models.Model):
    FACEBOOK = 'FB'
    TWITTER = 'TW'
    KAIST = 'KAIST'
    SOCIAL_TYPE = (
        (FACEBOOK, 'Facebook'),
        (TWITTER, 'Twitter'),
        (KAIST, 'KAIST SSO'),
    )

    userid = models.CharField(max_length=64)
    type = models.CharField(max_length=5, choices=SOCIAL_TYPE)
    email = models.CharField(max_length=100)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=64)
    gender = models.CharField(max_length=1, choices=GENDER, default=ETC)
