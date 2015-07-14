from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from apps.account.models import UserProfile, SocialSignupInfo, EmailAuthToken
from apps.account.forms import UserForm, UserProfileForm
import cgi
import json
import os
import re
import urllib
import datetime

# Helper functions
def parse_gender(gender):
    if gender == 'male':
        return 'M'
    elif gender == 'female':
        return 'F'
    else:
        return 'N'


def make_username():
    while True:
        username = os.urandom(10).encode('hex')
        if len(User.objects.filter(username=username)) == 0:
            return username


def make_token():
    while True:
        token = os.urandom(24).encode('hex')
        if len(EmailAuthToken.objects.filter(token=token)) == 0:
            return token


def get_username(email):
    user = User.objects.filter(email=email)
    if len(user) > 0:
        return user[0].username
    return ''


def validate_email(email, exclude=''):
    if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return False

    users = User.objects.filter(email=email).exclude(email=exclude)
    if len(users) > 0:
        return False
    return True


def authenticate_fb(request, token):
    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'client_secret': settings.FACEBOOK_APP_SECRET,
        'redirect_uri': request.build_absolute_uri('/account/login/fb/callback/'),
        'code': token,
    }

    target = urllib.urlopen('https://graph.facebook.com/oauth/access_token?' + urllib.urlencode(args)).read()
    response = cgi.parse_qs(target)
    access_token = response['access_token'][-1]

    fb_profile = urllib.urlopen('https://graph.facebook.com/me?access_token=%s' % access_token)
    fb_profile = json.load(fb_profile)

    try:
        user_profile = UserProfile.objects.get(facebook_id = fb_profile['id'])
        user_profile.facebook_token = access_token
        user_profile.save()

        return {'user': uesr_profile.user, 'fb_profile': fb_profile}
    except UserProfile.DoesNotExist:
        return {'user': None, 'fb_profile': fb_profile}


def email_auth(request, token):
    for token_element in EmailAuthToken.objects.filter(token=token):
        if token_element.expire_time.replace(tzinfo=None) >\
           datetime.datetime.now().replace(tzinfo=None) and\
           token_element.user_profile.email_authed == False:
            token_element.user_profile.email_authed = True
            token_element.user_profile.save()
            return redirect('/account/email-auth/success.html')
    return redirect('/account/email-auth/fail.html')

# Main screen
def main(request):
    if request.user.is_authenticated():
        return redirect('/account/profile/')
    return redirect('/account/login/')


# Email Login
def login_email(request):
    if request.user.is_authenticated():
        return redirect('/')

    if request.method == 'POST':
        email = request.POST.get('email', 'none')
        password = request.POST.get('password', 'asdf')
        nexturl = request.POST.get('next', '/')

        username = get_username(email)
        user = auth.authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return render(request, 'account/login.html',
                          {'next': nexturl, 'msg': 'Invalid Account Info'})
        elif not user.user_profile.email_authed:
            return render(request, 'account/email_reauth.html',
                          {'next': nexturl, 'msg': 'Reauth?'})
        else:
            auth.login(request, user)
            return redirect(nexturl)
    return render(request, 'account/login.html',
                  {'next': request.GET.get('next', '/')})


# Facebook login
def login_fb(request):
    if request.user.is_authenticated():
        return redirect('/')

    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'scope': 'email',
        'redirect_uri': request.build_absolute_uri('/account/login/fb/callback/'),
    }
    return redirect('https://www.facebook.com/dialog/oauth?' + urllib.urlencode(args))


# Facebook login callback
def login_fb_callback(request):
    if request.user.is_authenticated():
        return redirect('/')

    code = request.GET.get('code')
    data = authenticate_fb(request, code)
    
    if data['user'] is None:
        fb_profile = data['fb_profile']
        fb_signup_info = SocialSignupInfo.objects.filter(userid=fb_profile['id']).filter(type='FB').first()

        if fb_signup_info is None:
            fb_signup_info = SocialSignupInfo(userid=fb_profile['id'], type='FB', email=fb_profile['email'],
                                          first_name=fb_profile['first_name'],
                                          last_name=fb_profile['last_name'],
                                          gender=parse_gender(fb_profile['gender']))
            fb_signup_info.save()
        return redirect('/account/signup/fb/' + fb_signup_info.userid) 
    else:
        auth.login(request, user)
        return redirect('/')


# Twitter login
def login_tw(request):
    pass


# Twitter login callback
def login_tw_callback(request):
    pass


# Logout
def logout(request):
    if not request.user.is_authenticated():
        return redirect('/')

    auth.logout(request)
    return render(request, 'account/logout.html')


# Signup with email
def signup(request):
    if request.user.is_authenticated():
        return redirect('/')

    if request.method == 'POST':
        user_f = UserForm(request.POST)
        user_profile_f = UserProfileForm(request.POST)
        raw_email = request.POST.get('email', '')

        if validate_email(raw_email) and user_f.is_valid() \
                and user_profile_f.is_valid():
            email = user_f.cleaned_data['email']
            password = user_f.cleaned_data['password']
            first_name = user_f.cleaned_data['first_name']
            last_name = user_f.cleaned_data['last_name']

            tomorrow = datetime.datetime.now()\
                       + datetime.timedelta(days=1)

            username = make_username()
            user = User.objects.create_user(username=username,
                                            first_name=first_name,
                                            last_name=last_name,
                                            email=email, password=password)
            user.save()

            user_profile = user_profile_f.save(commit=False)
            user_profile.user = user

            token = make_token()
            email_auth_token = EmailAuthToken(token=token,
                                              expire_time=tomorrow)
            email_auth_token.user_profile = user_profile
            email_auth_token.save()

            user_profile.save()

            send_mail('[SPARCS SSO] E-mail Authorization',
                    'To get auth, please enter http://bit.sparcs.org'+
                    ':23232/account/email-auth/'+token,
                    'sparcssso@sparcs.org', [email])
        else:
            raise SuspiciousOperation("ERROR")
        return redirect('/')
    return render(request, 'account/signup.html')


# Signup with social account
def signup_social(request, userid, type):
    if request.user.is_authenticated():
        return redirect('/')
   
    signup_info = SocialSignupInfo.objects.filter(userid=userid).filter(type=type).first()
    if signup_info is None:
        raise Http404()

    if request.method == 'POST':
        pass

    return render(request, 'account/signup_social.html', {'info': signup_info})
    

# Email duplication check
def email_check(request):
    if validate_email(request.GET.get('email', ''),
                      request.GET.get('exclude', '')):
        return HttpResponse(status=200)
    return HttpResponse(status=400)


# View profile
@login_required
def profile(request):
    user = request.user
    userprofile = UserProfile.objects.get(user=user)

    msg = ''
    if request.method == "POST":
        user_f = UserForm(request.POST)
        user_profile_f = UserProfileForm(request.POST, instance=userprofile)
        raw_email = request.POST.get('email', '')

        if validate_email(raw_email, user.email) and user_f.is_valid() \
                and user_profile_f.is_valid():
            user.email = user_f.cleaned_data['email']
            user.first_name = user_f.cleaned_data['first_name']
            user.last_name = user_f.cleaned_data['last_name']
            user.save()

            userprofile = user_profile_f.save()
            msg = 'Your profile was successfully modified!'

    return render(request, 'account/profile.html',
                  {'user': user, 'userprofile': userprofile, 'msg': msg})


# Password change
@login_required
def password_change(request):
    user = request.user

    msg = ''
    if request.method == "POST":
        oldpw = request.POST.get('oldpassword', '')
        newpw = request.POST.get('password', 'P@55w0rd!#$')

        if check_password(oldpw, user.password):
            user.password = make_password(newpw)
            user.save()
            return redirect('/account/login')
        else:
            msg = 'Wrong current password.'

    return render(request, 'account/changepw.html', {'user': user, 'msg': msg})


# Password reset
@login_required
def password_reset(request):
    pass
