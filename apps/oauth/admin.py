from django.contrib import admin
from apps.oauth.models import AccessToken, Service


class UserFilter(admin.SimpleListFilter):
    title = 'user'
    parameter_name = 'user'

    def lookups(self, request, model_admin):
        users = [u.user for u in model_admin.model.objects.all()]
        users = list(set(users))
        return [(u.id, u.last_name + ' ' + u.first_name) for u in users]

    def queryset(self, request, qs):
        if self.value():
            return qs.filter(user__id__exact=self.value())
        else:
            return qs


class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('uid', 'user')
    list_filter = (UserFilter, )


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'alias', 'url', 'callback_url')


admin.site.register(Service, ServiceAdmin)
admin.site.register(AccessToken, AccessTokenAdmin)
