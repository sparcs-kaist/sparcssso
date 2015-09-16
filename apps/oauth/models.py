from django.db import models
from django.contrib.auth.models import User


class AccessToken(models.Model):
    uid = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(User)


class Service(models.Model):
    name = models.CharField(max_length=20, primary_key=True)
    alias = models.CharField(max_length=30)
    url = models.CharField(max_length=200)
    callback_url = models.CharField(max_length=200)
    icon = models.ImageField()
