from django.db import models
from django.contrib.auth.models import User


class AccessToken(models.Model):
    uid = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(User)
