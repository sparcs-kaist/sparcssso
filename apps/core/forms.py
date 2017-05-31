from django.contrib.auth.models import User
from django.forms import ModelForm

from .models import Service, UserProfile


class UserForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')


class UserProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['gender'].required = False
        self.fields['birthday'].required = False

    class Meta:
        model = UserProfile
        fields = ('gender', 'birthday')


class ServiceForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Service
        fields = (
            'alias', 'main_url', 'login_callback_url',
            'unregister_url', 'cooltime',
        )
