from django.contrib import admin
from apps.oauth.models import Service, ServiceMap, AccessToken


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
    list_display = ('tokenid', 'user', 'service')
    list_filter = (UserFilter, )


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_public', 'alias', 'url', 'callback_url',\
        'unregister_url', 'cooltime')


class ServiceMapAdmin(admin.ModelAdmin):
    list_display = ('sid', 'user', 'service', \
        'register_time', 'unregister_time')


admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceMap, ServiceMapAdmin)
admin.site.register(AccessToken, AccessTokenAdmin)
