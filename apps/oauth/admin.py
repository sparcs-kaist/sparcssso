from django.contrib import admin
from apps.oauth.models import AccessToken


class UserFilter(admin.SimpleListFilter):
    title = 'user'
    parameter_name = 'user'

    def lookups(self, request, model_admin):
        return [(u.user.id, u.user.last_name + ' ' + u.user.first_name)
                for u in model_admin.model.objects.all()]

    def queryset(self, request, qs):
        if self.value():
            return qs.filter(user__id__exact=self.value())
        else:
            return qs


class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('uid', 'user')
    list_filter = (UserFilter, )


admin.site.register(AccessToken, AccessTokenAdmin)
