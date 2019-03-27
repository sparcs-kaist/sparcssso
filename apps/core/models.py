import json

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.timezone import localtime


SERVICE_PUBLIC = 'PUBLIC'
SERVICE_SPARCS = 'SPARCS'
SERVICE_TEST = 'TEST'
SERVICE_SCOPE = (
    (SERVICE_PUBLIC, 'Public'),
    (SERVICE_SPARCS, 'SPARCS'),
    (SERVICE_TEST, 'Test'),
)

User.__str__ = lambda s: f'{s.first_name} {s.last_name} <{s.username}>'


# == General Objects ==
class Notice(models.Model):
    """
    denotes single notice
    - title:      notice title
    - valid_from: display start time
    - valid_to:   display end time
    - text:       notice content; html
    """
    title = models.CharField(max_length=100)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    text = models.TextField()

    def to_dict(self):
        return {
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat(),
            'title': self.title,
            'text': self.text,
        }

    def __str__(self):
        return self.title


class Statistic(models.Model):
    """
    denotes single statistic; raw json
    - time: timestamp of statistic
    - data: raw json statistic data
    """
    time = models.DateTimeField()
    data = models.TextField()

    def pretty(self):
        time_str = localtime(self.time).isoformat()
        return f'{time_str} {self.data}'

    def __str__(self):
        return f'{self.time}'


class Document(models.Model):
    """
    denotes single documents that used by terms and privacy policy
    - category:     terms / privacy policy
    - version:      simple version; v1.x
    - date_apply:   apply date
    - date_version: detail version; date format
    - text:         doc content; special markdown
    """
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
                result.append(f'<h3>{line[depth:]}</h3>')
            else:
                result.append(f'<li>{line[depth:]}</li>')
        result.append('</ol>' * depth)
        return '\n'.join(result)

    def __str__(self):
        return f'{self.category} - {self.version}'


# == Service Related Objects ==
class Service(models.Model):
    """
    denotes single sso client
    - name:               unique name
    - is_shown:           decides to show in SSO main page
    - alias:              user friendly name
    - scope:              scope; TEST / SPARCS / PUBLIC
    - main_url:           main page url
    - login_callback_url: login callback url
    - unregister_url:     unregister page url
    - secret_key:         secret key
    - admin_user:         admin of this client
    - cooltime:           cooltime (days) to re-register; < 60
    - icon:               icon of this service
    """

    name = models.CharField(max_length=20, primary_key=True)
    is_shown = models.BooleanField(default=True)
    alias = models.CharField(max_length=30)
    scope = models.CharField(max_length=6, choices=SERVICE_SCOPE,
                             default=SERVICE_TEST)
    main_url = models.CharField(max_length=200)
    login_callback_url = models.CharField(max_length=200)
    unregister_url = models.CharField(max_length=200, null=True, blank=True)
    secret_key = models.CharField(max_length=100)
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='managed_services')
    cooltime = models.IntegerField()
    icon = models.ImageField(null=True, blank=True)

    @property
    def icon_url(self):
        return self.icon.url if self.icon else '/static/img/test-service.png'

    def __str__(self):
        return self.alias


class ServiceMap(models.Model):
    """
    denotes single (user, service) pair
    - sid:             unique mapping id
    - user:            user object
    - service:         service object
    - register_time:   register time
    - unregister_time: unregister time
    """
    sid = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    register_time = models.DateTimeField()
    unregister_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user} - {self.service}'


class AccessToken(models.Model):
    """
    denotes single access token of (user, service) pair
    - tokenid:     unique token id
    - user:        user object
    - service:     service object
    - expire_time: expire time
    """
    tokenid = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    expire_time = models.DateTimeField()

    def __str__(self):
        return f'{self.user} - {self.service}'


# == User Related Objects ==
class UserProfile(models.Model):
    """
    denotes additional information of single user
    - user:            user object
    - gender:          gender; *H / *M / *F / *E or others
    - birthday:        birthday
    - point:           point for public services
    - point_test:      point for test services
    - email_new:       new email before auth
    - email_authed:    email authed state
    - test_only:       indicate test only account
    - test_enabled:    test mode state
    - facebook_id:     facebook unique id
    - twitter_id:      twitter unique id
    - kaist_id:        kaist uid
    - kaist_info:      additional kaist info
    - kaist_info_time: kaist info updated time
    - sparcs_id:       sparcs id iff sparcs member
    - expire_time:     expire time for permanent deletion
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='profile')
    gender = models.CharField(max_length=30)
    birthday = models.DateField(blank=True, null=True)
    point = models.IntegerField(default=0)
    point_test = models.IntegerField(default=0)
    email_new = models.EmailField(blank=True, null=True)
    email_authed = models.BooleanField(default=False)
    test_only = models.BooleanField(default=False)
    test_enabled = models.BooleanField(default=False)
    facebook_id = models.CharField(max_length=50, blank=True, null=True)
    twitter_id = models.CharField(max_length=50, blank=True, null=True)
    kaist_id = models.CharField(max_length=50, blank=True, null=True)
    kaist_info = models.TextField(blank=True, null=True)
    kaist_info_time = models.DateField(blank=True, null=True)
    sparcs_id = models.CharField(max_length=50, blank=True, null=True)
    expire_time = models.DateTimeField(blank=True, null=True)

    @property
    def flags(self):
        return {
            'test': self.test_enabled,
            'test-only': self.test_only,
            'dev': self.user.is_staff or bool(self.sparcs_id),
            'sparcs': bool(self.sparcs_id),
            'sysop': self.user.is_staff,
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

    def save_kaist_info(self, info):
        self.kaist_id = info['userid']
        self.kaist_info = json.dumps(info['kaist_info'])
        self.kaist_info_time = timezone.now()
        self.save()

    def __str__(self):
        return f'{self.user}''s profile'


class EmailAuthToken(models.Model):
    """
    denotes single email auth token for an user
    - tokenid:     unique token id
    - user:        user object
    - expire_time: expire time; < 24 hours
    """
    tokenid = models.CharField(max_length=48, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expire_time = models.DateTimeField()

    def __str__(self):
        return f'{self.user} - {self.tokenid}'


class ResetPWToken(models.Model):
    """
    denotes single password reset token for an user
    - tokenid:     unique token id
    - user:        user object
    - expire_time: expire time; < 24 hours
    """
    tokenid = models.CharField(max_length=48, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expire_time = models.DateTimeField()

    def __str__(self):
        return f'{self.user} - {self.tokenid}'


class PointLog(models.Model):
    """
    denotes single point log for a user
    - user:    user object
    - service: service object
    - time:    event time
    - delta:   change of point
    - point:   total point after delta
    - action:  detail log message
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='point_logs')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now=True)
    delta = models.IntegerField()
    point = models.IntegerField()
    action = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.user} / {self.service} - {self.delta}'


class UserLog(models.Model):
    """
    denotes single log for an user or global event
    - user:  user object
    - level: level of log; python log level
    - time:  event time
    - ip:    event ip
    - hide:  hide log in user log page
    - text:  detail log message
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='user_logs', blank=True, null=True)
    level = models.IntegerField()
    time = models.DateTimeField(auto_now=True)
    ip = models.GenericIPAddressField()
    hide = models.BooleanField(default=False)
    text = models.CharField(max_length=500)

    def pretty(self):
        time = localtime(self.time).isoformat()
        username = self.user.username if self.user else 'unknown'
        level, ip, text = self.level, self.ip, self.text
        return f'{time}/{level} ({ip}, {username}) {text}'

    def __str__(self):
        time_str = localtime(self.time).isoformat()
        return f'{time_str}/{self.level} ({self.user}) {self.text}'


class EmailDomain(models.Model):
    """
    denotes an email domain
    - domain:    the email domain
    - is_banned: banned status
    """
    domain = models.CharField(max_length=100, unique=True)
    is_banned = models.BooleanField(default=True)


class LoginFailureLog(models.Model):
    """
    denotes single log of an user for login failure event.
    used to prevent the system from bruteforcing attack via login form.
    - ip: origin ip address
    - username: attmpted username at failure, this can be empty
    - time: timestamp (indexed for later query)
    """
    ip = models.GenericIPAddressField()
    username = models.CharField(max_length=127)
    time = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        time_str = localtime(self.time).isoformat()
        return f'{self.username} {self.ip} {time_str}'
