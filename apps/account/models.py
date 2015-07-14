from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    MALE = 'M'
    FEMALE = 'F'
    NONE = 'N'
    GENDER = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
        (NONE, 'None'),
    )
    user = models.OneToOneField(User)
    gender = models.CharField(max_length=1, choices=GENDER, default=NONE)
    birthday = models.DateField(blank=True, null=True)
    email_authed = models.BooleanField(default=False)
    facebook_id = models.CharField(max_length=50, blank=True, null=True)
    facebook_token = models.CharField(max_length=255, blank=True, null=True)

class EmailAuthToken(models.Model):
    user = models.OneToOneField(User)
    token = models.CharField(max_length=32, primary_key=True)
    expire = models.DateField()
