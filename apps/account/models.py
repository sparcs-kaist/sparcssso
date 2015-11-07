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
    tokenid = models.CharField(max_length=48, primary_key=True)
    expire_time = models.DateTimeField()
    user = models.ForeignKey(User)


class ResetPWToken(models.Model):
    tokenid = models.CharField(max_length=48, primary_key=True)
    expire_time = models.DateTimeField()
    user = models.ForeignKey(User)


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    gender = models.CharField(max_length=1, choices=GENDER, default=ETC)
    birthday = models.DateField(blank=True, null=True)
    email_authed = models.BooleanField(default=False)
    is_for_test = models.BooleanField(default=False)
    facebook_id = models.CharField(max_length=50, blank=True, null=True)
    twitter_id = models.CharField(max_length=50, blank=True, null=True)
    kaist_id = models.CharField(max_length=50, blank=True, null=True)
    kaist_info = models.TextField(blank=True, null=True)
    expire_time = models.DateTimeField(blank=True, null=True)


class Notice(models.Model):
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    title = models.CharField(max_length=100)
    text = models.TextField()
