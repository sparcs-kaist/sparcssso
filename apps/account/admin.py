from django.contrib import admin
from django.contrib.auth.models import User
from apps.account.models import UserProfile, EmailAuthToken, ResetPWToken, Notice


def get_profile(obj):
    return UserProfile.objects.get(user=obj)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'user profile'


class UserAdmin(admin.ModelAdmin):
    def get_name(self, obj):
        return obj.last_name + ' ' + obj.first_name
    get_name.admin_order_field = 'last_name'
    get_name.short_description = 'Name'

    def get_gender(self, obj):
        return get_profile(obj).get_gender_display()
    get_gender.short_description = 'Gender'

    def get_email_authed(self, obj):
        return get_profile(obj).email_authed
    get_email_authed.short_description = 'Email Authed'
    get_email_authed.boolean = True

    def get_is_for_test(self, obj):
        return get_profile(obj).is_for_test
    get_is_for_test.short_description = 'Test Account'
    get_is_for_test.boolean = True

    list_display = ('email', 'username', 'get_name', 'get_gender',
                    'get_email_authed', 'get_is_for_test')
    inlines = (UserProfileInline, )
    list_filter = ('is_staff', )


class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'valid_from', 'valid_to', 'text')


class EmailAuthTokenAdmin(admin.ModelAdmin):
    list_display = ('tokenid', 'expire_time', 'user')


class ResetPWTokenAdmin(admin.ModelAdmin):
    list_display = ('tokenid', 'expire_time', 'user')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Notice, NoticeAdmin)
admin.site.register(EmailAuthToken, EmailAuthTokenAdmin)
admin.site.register(ResetPWToken, ResetPWTokenAdmin)
