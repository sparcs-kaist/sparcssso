from django.contrib import admin
from django.contrib.auth import admin as uadmin
from django.contrib.auth.models import User
from apps.core.models import Notice, Statistic, Document, Service, \
    ServiceMap, AccessToken, UserProfile, EmailAuthToken, ResetPWToken, \
    PointLog, UserLog


# Filters
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


# Admin for General Objects
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'valid_from', 'valid_to', 'text')


class StatisticAdmin(admin.ModelAdmin):
    list_display = ('time', 'data')


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('category', 'version', 'date_apply', 'date_version')


# Admin for Service Related Objects
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_shown', 'alias', 'scope', 'admin_user',
                    'main_url', 'login_callback_url', 'unregister_url', 'cooltime')


class ServiceMapAdmin(admin.ModelAdmin):
    list_display = ('sid', 'user', 'service',
                    'register_time', 'unregister_time')


class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('tokenid', 'user', 'service', 'expire_time')
    list_filter = (UserFilter, )


# Admin for User Related Objects
class UserAdmin(uadmin.UserAdmin):
    class UserProfileInline(admin.StackedInline):
        model = UserProfile
        can_delete = False
        fieldsets = (
            ('General', {
                'fields': (('gender', 'birthday'),
                           ('email_authed', 'password_set'), 'expire_time'),
            }),
            ('Points', {
                'fields': (('point', 'point_test'), ),
            }),
            ('SNS', {
                'fields': (('facebook_id', 'twitter_id'),
                           ('kaist_id', 'kaist_info_time'), 'kaist_info'),
            }),
            ('Debug', {
                'fields': (('sparcs_id', 'test_only', 'test_enabled'), ),
            }),
        )

    def get_profile(self, obj):
        return UserProfile.objects.get(user=obj)

    def get_name(self, obj):
        return obj.last_name + ' ' + obj.first_name
    get_name.admin_order_field = 'last_name'
    get_name.short_description = 'Name'

    def get_gender(self, obj):
        return self.get_profile(obj).gender_display()
    get_gender.short_description = 'Gender'

    def get_point(self, obj):
        return self.get_profile(obj).point
    get_point.short_description = 'Point'

    def get_email_authed(self, obj):
        return self.get_profile(obj).email_authed
    get_email_authed.short_description = 'Email Authed'
    get_email_authed.boolean = True

    def get_test_enabled(self, obj):
        return self.get_profile(obj).test_enabled
    get_test_enabled.short_description = 'Test Account'
    get_test_enabled.boolean = True

    list_display = ('email', 'username', 'get_name', 'get_gender', 'get_point',
                    'get_email_authed', 'get_test_enabled')
    list_filter = ('is_staff', )
    inlines = (UserProfileInline, )
    ordering = ()


class EmailAuthTokenAdmin(admin.ModelAdmin):
    list_display = ('tokenid', 'expire_time', 'user')


class ResetPWTokenAdmin(admin.ModelAdmin):
    list_display = ('tokenid', 'expire_time', 'user')


class PointLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'time', 'delta', 'action')


class UserLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'time', 'ip', 'text')


admin.site.unregister(User)
admin.site.register(Notice, NoticeAdmin)
admin.site.register(Statistic, StatisticAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceMap, ServiceMapAdmin)
admin.site.register(AccessToken, AccessTokenAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(EmailAuthToken, EmailAuthTokenAdmin)
admin.site.register(ResetPWToken, ResetPWTokenAdmin)
admin.site.register(PointLog, PointLogAdmin)
admin.site.register(UserLog, UserLogAdmin)
