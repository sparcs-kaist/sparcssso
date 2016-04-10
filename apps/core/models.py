from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


MALE = 'M'
FEMALE = 'F'
ETC = 'E'
GENDER = (
    (MALE, 'Male'),
    (FEMALE, 'Female'),
    (ETC, 'etc'),
)

User.__unicode__ = lambda self: u'%s %s <%s>' % \
        (self.first_name, self.last_name, self.username)


# General Objects
class Notice(models.Model):
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    title = models.CharField(max_length=100)
    text = models.TextField()

    def to_dict(self):
        return {
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat(),
            'title': self.title,
            'text': self.text,
        }

    def __unicode__(self):
        return self.title


# Service Related Objects
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

    def __unicode__(self):
        return self.alias


class ServiceMap(models.Model):
    sid = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(User, related_name='services')
    service = models.ForeignKey(Service)
    register_time = models.DateTimeField()
    unregister_time = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return u'%s - %s' % (self.service, self.user)


class AccessToken(models.Model):
    tokenid = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(User)
    service = models.ForeignKey(Service, null=True, blank=True)
    expire_time = models.DateTimeField()

    def __unicode__(self):
        return u'%s - %s' % (self.service, self.user)


# User Related Objects
class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    gender = models.CharField(max_length=1, choices=GENDER, default=ETC)
    birthday = models.DateField(blank=True, null=True)
    point = models.IntegerField(default=0)
    email_authed = models.BooleanField(default=False)
    is_for_test = models.BooleanField(default=False)
    facebook_id = models.CharField(max_length=50, blank=True, null=True)
    twitter_id = models.CharField(max_length=50, blank=True, null=True)
    kaist_id = models.CharField(max_length=50, blank=True, null=True)
    kaist_info = models.TextField(blank=True, null=True)
    kaist_info_time = models.DateField(blank=True, null=True)
    sparcs_id = models.CharField(max_length=50, blank=True, null=True)
    expire_time = models.DateTimeField(blank=True, null=True)

    def activate(self):
        if self.expire_time:
            self.expire_time = None
            self.save()
            return True
        return False

    def set_kaist_info(self, info):
        self.kaist_id = info['userid']
        self.kaist_info = json.dumps(info['kaist_info'])
        self.kaist_info_time = timezone.now()
        self.save()

    def __unicode__(self):
        return u'%s''s profile' % self.user


class EmailAuthToken(models.Model):
    tokenid = models.CharField(max_length=48, primary_key=True)
    expire_time = models.DateTimeField()
    user = models.ForeignKey(User)

    def __unicode__(self):
        return u'%s - %s' % (self.user, self.tokenid)


class ResetPWToken(models.Model):
    tokenid = models.CharField(max_length=48, primary_key=True)
    expire_time = models.DateTimeField()
    user = models.ForeignKey(User)

    def __unicode__(self):
        return u'%s - %s' % (self.user, self.tokenid)


class PointLog(models.Model):
    user = models.ForeignKey(User, related_name='point_logs')
    service = models.ForeignKey(Service)
    time = models.DateTimeField(auto_now=True)
    delta = models.IntegerField()
    point = models.IntegerField()
    action = models.CharField(max_length=200)

    def __unicode__(self):
        return u'%s - %d by %s' % (self.user, self.delta, self.service)


class UserLog(models.Model):
    user = models.ForeignKey(User, related_name='user_logs')
    level = models.IntegerField()
    time = models.DateTimeField(auto_now=True)
    ip = models.GenericIPAddressField()
    text = models.CharField(max_length=500)
