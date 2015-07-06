from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import render, redirect
from django.http import HttpResponse
from apps.session.models import UserProfile
from apps.session.forms import UserForm, UserProfileForm
import re
import os


def make_username():
    while True:
        username = os.urandom(10).encode('hex')
        if len(User.objects.filter(username=username)) == 0:
            return username


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


def email_check(request):
    if validate_email(request.GET.get('email', ''),
                      request.GET.get('exclude', '')):
        return HttpResponse(status=200)
    return HttpResponse(status=400)


def login(request):
    if request.user.is_authenticated():
        return redirect('/')

    if request.method == 'POST':
        email = request.POST.get('email', 'none')
        password = request.POST.get('password', 'asdf')
        nexturl = request.POST.get('next', '/')

        username = get_username(email)
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            return redirect(nexturl)
        else:
            return render(request, 'session/login.html',
                          {'next': nexturl, 'msg': 'Invalid Account Info'})
    return render(request, 'session/login.html',
                  {'next': request.GET.get('next', '/')})


def logout(request):
    if not request.user.is_authenticated():
        return redirect('/')

    auth.logout(request)
    return render(request, 'session/logout.html')


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

            username = make_username()
            user = User.objects.create_user(username=username,
                                            first_name=first_name,
                                            last_name=last_name,
                                            email=email, password=password)
            user.save()

            user_profile = user_profile_f.save(commit=False)
            user_profile.user = user
            user_profile.save()
        else:
            raise SuspiciousOperation()
        return redirect('/')
    return render(request, 'session/signup.html')


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

    return render(request, 'session/profile.html',
                  {'user': user, 'userprofile': userprofile, 'msg': msg})


@login_required
def changepw(request, uid=''):
    user = request.user

    msg = ''
    if request.method == "POST":
        oldpw = request.POST.get('oldpassword', '')
        newpw = request.POST.get('password', 'P@55w0rd!#$')

        if check_password(oldpw, user.password):
            user.password = make_password(newpw)
            user.save()
            return redirect('/session/login')
        else:
            msg = 'Wrong current password.'

    return render(request, 'session/changepw.html', {'user': user, 'msg': msg})


def main(request):
    if request.user.is_authenticated():
        return redirect('/session/profile/')
    return redirect('/session/login/')
