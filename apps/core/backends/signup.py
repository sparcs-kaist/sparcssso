from secrets import token_hex

from django.contrib.auth.models import User

from .token import token_issue_email_auth
from .util import validate_email
from ..forms import UserForm
from ..models import UserProfile


# signup using email
def signup_email(post):
    user_f = UserForm(post)
    raw_email = post.get('email', '')

    if not user_f.is_valid() or not validate_email(raw_email):
        return None

    email = user_f.cleaned_data['email']
    password = user_f.cleaned_data['password']
    first_name = user_f.cleaned_data['first_name']
    last_name = user_f.cleaned_data['last_name']
    while True:
        username = token_hex(10)
        if not User.objects.filter(username=username).count():
            break

    user = User.objects.create_user(username=username,
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=email,
                                    password=password)
    user.save()
    UserProfile(user=user, gender='*H').save()

    token_issue_email_auth(user, newbie=True)
    return user


# signup using social
def signup_social(type, profile):
    while True:
        username = token_hex(10)
        if not User.objects.filter(username=username).count():
            break

    first_name = profile.get('first_name', '')
    last_name = profile.get('last_name', '')

    email = profile.get('email', '')
    if not email:
        email = f'random-{token_hex(6)}@sso.sparcs.org'

    while True:
        if not User.objects.filter(email=email).count():
            break
        email = f'random-{token_hex(6)}@sso.sparcs.org'

    user = User.objects.create_user(username=username,
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=email)
    user.save()

    user.profile = UserProfile(gender=profile.get('gender', '*H'))
    if 'birthday' in profile:
        user.profile.birthday = profile['birthday']

    if type == 'FB':
        user.profile.facebook_id = profile['userid']
    elif type == 'TW':
        user.profile.twitter_id = profile['userid']
    elif type == 'KAIST':
        user.profile.email_authed = email.endswith('@kaist.ac.kr')
        user.profile.save_kaist_info(profile)
    user.profile.save()
    return user
