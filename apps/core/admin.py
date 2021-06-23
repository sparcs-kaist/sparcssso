from django.contrib import admin
from django.contrib.auth import admin as uadmin
from django.contrib.auth.models import User

from apps.core.models import (
    AccessToken, Document, EmailAuthToken, EmailDomain, InquiryMail, Notice,
    PointLog, ResetPWToken, Service, ServiceMap,
    Statistic, UserLog, UserProfile,
)


admin.site.unregister(User)


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
@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'valid_from', 'valid_to', 'text')


@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ('time', 'data')
    readonly_fields = list(map(lambda x: x.name, Statistic._meta.fields))

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('category', 'version', 'date_apply', 'date_version')


# Admin for Service Related Objects
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_shown', 'alias', 'scope',
                    'admin_user', 'main_url', 'login_callback_url',
                    'unregister_url', 'cooltime')


@admin.register(ServiceMap)
class ServiceMapAdmin(admin.ModelAdmin):
    actions = None
    list_display = ('sid', 'user', 'service',
                    'register_time', 'unregister_time')
    readonly_fields = ('user', 'service', 'sid')
    search_fields = ('user__email', 'service__name', 'service__alias')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('tokenid', 'user', 'service', 'expire_time')
    list_filter = (UserFilter, )
    readonly_fields = list(map(lambda x: x.name, AccessToken._meta.fields))

    def has_add_permission(self, request, obj=None):
        return False


# Admin for User Related Objects
@admin.register(User)
class UserAdmin(uadmin.UserAdmin):
    class UserProfileInline(admin.StackedInline):
        model = UserProfile
        can_delete = False
        fieldsets = (
            ('General', {
                'fields': ('gender', 'birthday',
                           'email_authed', 'expire_time'),
            }),
            ('Points', {
                'fields': ('point', 'point_test'),
            }),
            ('SNS', {
                'fields': ('facebook_id', 'twitter_id',
                           'kaist_id', 'kaist_info_time', 'kaist_info'),
            }),
            ('Dev / Debug', {
                'fields': ('sparcs_id', 'test_only', 'test_enabled'),
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


@admin.register(EmailAuthToken)
class EmailAuthTokenAdmin(admin.ModelAdmin):
    list_display = ('tokenid', 'expire_time', 'user')
    readonly_fields = list(map(lambda x: x.name, EmailAuthToken._meta.fields))

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ResetPWToken)
class ResetPWTokenAdmin(admin.ModelAdmin):
    list_display = ('tokenid', 'expire_time', 'user')
    readonly_fields = list(map(lambda x: x.name, ResetPWToken._meta.fields))

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PointLog)
class PointLogAdmin(admin.ModelAdmin):
    actions = None
    list_display = ('user', 'service', 'time', 'delta', 'action')
    readonly_fields = list(map(lambda x: x.name, PointLog._meta.fields))

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    actions = None
    list_display = ('user', 'level', 'time', 'ip', 'text')
    readonly_fields = list(map(lambda x: x.name, UserLog._meta.fields))

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EmailDomain)
class EmailDomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'is_banned')
    search_fields = ('domain', )
    ordering = ('domain', )


@admin.register(InquiryMail)
class InquiryMailAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'user', 'topic', 'title')
    fields = ('created_at', 'user', 'name', 'email', 'topic', 'title', 'content')
    readonly_fields = fields
