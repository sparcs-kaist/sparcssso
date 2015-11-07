from django.db import models
from django.contrib.auth.models import User


class Service(models.Model):
    name = models.CharField(max_length=20, primary_key=True)
    is_public = models.BooleanField(default=True)
    alias = models.CharField(max_length=30)
    url = models.CharField(max_length=200)
    callback_url = models.CharField(max_length=200)
    unregister_url = models.CharField(max_length=200)
    secret_key = models.CharField(max_length=100)
    cooltime = models.IntegerField()
    icon = models.ImageField()


class ServiceMap(models.Model):
    sid = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(User)
    service = models.ForeignKey(Service)
    register_time = models.DateTimeField()
    unregister_time = models.DateTimeField(null=True, blank=True)


class AccessToken(models.Model):
    tokenid = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(User)
    service = models.ForeignKey(Service, null=True, blank=True)
