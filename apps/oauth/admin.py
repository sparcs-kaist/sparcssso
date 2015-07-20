from django.contrib import admin
from apps.oauth.models import AccessToken

admin.site.register(AccessToken)
