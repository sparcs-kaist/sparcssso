from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import localtime
import json


SERVICE_PUBLIC = 'PUBLIC'
SERVICE_SPARCS = 'SPARCS'
SERVICE_TEST = 'TEST'
SERVICE_SCOPE = (
    (SERVICE_PUBLIC, 'Public'),
    (SERVICE_SPARCS, 'SPARCS'),
    (SERVICE_TEST, 'Test'),
)

User.__str__ = lambda self: '{} {} <{}>'.format(
    self.first_name, self.last_name, self.username
)


# == General Objects ==
# Notice: denotes single notice
class Notice(models.Model):
    title = models.CharField(max_length=100)  # notice title
    valid_from = models.DateTimeField()       # display start time
    valid_to = models.DateTimeField()         # display end time
    text = models.TextField()                 # notice content

    def to_dict(self):
        return {
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat(),
            'title': self.title,
            'text': self.text,
        }

    def __str__(self):
        return self.title


# Statistic: denotes single raw json type statistic
class Statistic(models.Model):
    time = models.DateTimeField()  # timestamp
    data = models.TextField()      # raw json data

    def pretty(self):
        time_str = localtime(self.time).isoformat()
        return '{} {}'.format(time_str, self.data)

    def __str__(self):
        return '{}'.format(self.time)


# Document: denotes single documents that used by terms and privacy policy
class Document(models.Model):
    category = models.CharField(max_length=20)
    version = models.CharField(max_length=20)
    date_apply = models.DateTimeField()
    date_version = models.DateTimeField()
    text = models.TextField()

    class Meta:
        unique_together = ('category', 'version')

    def to_html(self):
        lines = map(lambda x: x.strip(), self.text.split('\n'))
        depth = 1
        result = []
        for line in lines:
            cur_depth = line.find(' ')
            diff = cur_depth - depth
            if diff > 0:
                result.append('<ol>' * diff)
            elif diff < 0:
                result.append('</ol>' * abs(diff))
            depth = cur_depth
            if depth == 1:
                result.append('<h3>%s</h3>' % line[depth:])
            else:
                result.append('<li>%s</li>' % line[depth:])
        result.append('</ol>' * depth)
        return '\n'.join(result)

    def __str__(self):
        return '{} / {}'.format(self.category, self.version)


# == Service Related Objects ==
# Service: denotes single sso client
class Service(models.Model):
    name = models.CharField(max_length=20, primary_key=True)         # unique name
    is_shown = models.BooleanField(default=True)                     # decides to show in main page
    alias = models.CharField(max_length=30)                          # name for human
    scope = models.CharField(max_length=6,
                             choices=SERVICE_SCOPE,
                             default=SERVICE_TEST)                   # scope of service
    main_url = models.CharField(max_length=200)                      # main
    login_callback_url = models.CharField(max_length=200)            # login callback url
    unregister_url = models.CharField(max_length=200)                # unregister check url
    secret_key = models.CharField(max_length=100)                    # secret key
    admin_user = models.ForeignKey(User,
                                   related_name='managed_services')  # admin of service
    cooltime = models.IntegerField()                                 # cooltime for re-register
    icon = models.ImageField(null=True, blank=True)                  # icon of the service

    @property
    def icon_url(self):
        return self.icon.url if self.icon else '/static/img/test-service.png'

    def __str__(self):
        return self.alias


# ServiceMap: denotes single (user, service) pair
class ServiceMap(models.Model):
    sid = models.CharField(max_length=20, primary_key=True)        # unique mapping id
    user = models.ForeignKey(User, related_name='services')        # user object
    service = models.ForeignKey(Service)                           # service object
    register_time = models.DateTimeField()                         # register time
    unregister_time = models.DateTimeField(null=True, blank=True)  # unregister time

    def __str__(self):
        return '{} - {}'.format(self.user, self.service)


# AccessToken: denotes single access token of (user, service) pair
class AccessToken(models.Model):
    tokenid = models.CharField(max_length=20, primary_key=True)  # unique token id
    user = models.ForeignKey(User)                               # user object
    service = models.ForeignKey(Service, null=True, blank=True)  # service object
    expire_time = models.DateTimeField()                         # expire time

    def __str__(self):
        return '{} - {}'.format(self.user, self.service)


# == User Related Objects ==
# UserProfile: denotes additional information of single user
class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile')             # user object
    gender = models.CharField(max_length=30)                              # gender
    birthday = models.DateField(blank=True, null=True)                    # birthday
    point = models.IntegerField(default=0)                                # point
    point_test = models.IntegerField(default=0)                           # point for test
    email_authed = models.BooleanField(default=False)                     # email authed state
    password_set = models.BooleanField(default=True)                      # indicate password set
    test_only = models.BooleanField(default=False)                        # indicate test only
    test_enabled = models.BooleanField(default=False)                     # test mode state
    facebook_id = models.CharField(max_length=50, blank=True, null=True)  # fb unique id
    twitter_id = models.CharField(max_length=50, blank=True, null=True)   # tw unique id
    kaist_id = models.CharField(max_length=50, blank=True, null=True)     # kaist uid
    kaist_info = models.TextField(blank=True, null=True)                  # additional kaist info
    kaist_info_time = models.DateField(blank=True, null=True)             # kaist info updated time
    sparcs_id = models.CharField(max_length=50, blank=True, null=True)    # sparcs id
    expire_time = models.DateTimeField(blank=True, null=True)             # expire time

    @property
    def flags(self):
        return {
            'test': self.test_enabled,
            'test-only': self.test_only,
            'dev': self.user.is_staff or bool(self.sparcs_id),
            'sparcs': bool(self.sparcs_id),
            'sysop': self.user.is_staff
        }

    def gender_display(self):
        if self.gender == '*M':
            return 'Male'
        elif self.gender == '*F':
            return 'Female'
        elif self.gender == '*H':
            return 'Hide'
        elif self.gender == '*E':
            return 'etc'
        return self.gender

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

    def __str__(self):
        return '{}''s profile'.format(self.user)


# EmailAuthToken: denotes single email auth token for an user
class EmailAuthToken(models.Model):
    tokenid = models.CharField(max_length=48, primary_key=True)  # unique token id
    user = models.ForeignKey(User)                               # user object
    expire_time = models.DateTimeField()                         # expire time

    def __str__(self):
        return '{} - {}'.format(self.user, self.tokenid)


# ResetPWToken: denotes single password reset token for an user
class ResetPWToken(models.Model):
    tokenid = models.CharField(max_length=48, primary_key=True)  # unique token id
    user = models.ForeignKey(User)                               # user object
    expire_time = models.DateTimeField()                         # expire time

    def __str__(self):
        return '{} - {}'.format(self.user, self.tokenid)


# PointLog: denotes single point log for a (user, service) pair
class PointLog(models.Model):
    user = models.ForeignKey(User, related_name='point_logs')  # user object
    service = models.ForeignKey(Service)                       # service object
    time = models.DateTimeField(auto_now=True)                 # event time
    delta = models.IntegerField()                              # delta point
    point = models.IntegerField()                              # total point
    action = models.CharField(max_length=200)                  # log message

    def __str__(self):
        return '{} / {} - {}'.format(self.user, self.service, self.delta)


# UserLog: denotes single user log for an user / (or global)
class UserLog(models.Model):
    user = models.ForeignKey(User, related_name='user_logs',  # user object
                             blank=True, null=True)
    level = models.IntegerField()                             # level
    time = models.DateTimeField(auto_now=True)                # event time
    ip = models.GenericIPAddressField()                       # event ip
    hide = models.BooleanField(default=False)                 # hide log to users
    text = models.CharField(max_length=500)                   # log message

    def pretty(self):
        time_str = localtime(self.time).isoformat()
        return '{}/{} ({}, {}) {}'.format(time_str, self.level, self.ip,
                                          self.user.username, self.text)

    def __str__(self):
        time_str = localtime(self.time).isoformat()
        return '{}/{} ({}) {}'.format(time_str, self.level,
                                      self.user, self.text)
