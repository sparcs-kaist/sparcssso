from django.forms import ModelForm
from django.contrib.auth.models import User
from apps.session.models import UserProfile


class UserForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')


class UserProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)

    class Meta:
        model = UserProfile
        fields = ('gender', 'birthday')
