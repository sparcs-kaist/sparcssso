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
