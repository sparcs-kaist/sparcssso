from django.db import models
from django.contrib.auth.models import User
from apps.oauth.models import Service


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

    def __unicode__(self):
        return u'%s''s profile' % self.user


class PointLog(models.Model):
    user = models.ForeignKey(User, related_name='point_logs')
    service = models.ForeignKey(Service)
    time = models.DateTimeField(auto_now=True)
    delta = models.IntegerField()
    point = models.IntegerField()
    action = models.CharField(max_length=200)

    def __unicode__(self):
        return u'%s - %d by %s' % (self.user, self.delta, self.service)


class Notice(models.Model):
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    title = models.CharField(max_length=100)
    text = models.TextField()

    def __unicode__(self):
        return self.title
