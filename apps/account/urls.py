from django.conf.urls import url

urlpatterns = [
    url(r'^$', 'apps.account.views.profile'),

    # login & logout section
    url(r'^login/$', 'apps.account.views.login'),
    url(r'^login/fb/$', 'apps.account.views.auth_init', {'mode': 'LOGIN', 'type': 'FB'}),
    url(r'^login/tw/$', 'apps.account.views.auth_init', {'mode': 'LOGIN', 'type': 'TW'}),
    url(r'^login/kaist/$', 'apps.account.views.auth_init', {'mode': 'LOGIN', 'type': 'KAIST'}),
    url(r'^logout/$', 'apps.account.views.logout'),

    # auth section
    url(r'^auth/email/$', 'apps.account.views.auth_email_resend'),
    url(r'^auth/email/(?P<tokenid>\w+)$', 'apps.account.views.auth_email'),

    # profile section
    url(r'^profile/$', 'apps.account.views.profile'),

    # password section
    url(r'^password/change/$', 'apps.account.views.password_change'),
    url(r'^password/reset/$', 'apps.account.views.password_reset_email'),
    url(r'^password/reset/(?P<tokenid>\w+)$', 'apps.account.views.password_reset'),

    # signup section
    url(r'^signup/$', 'apps.account.views.signup'),
    url(r'^signup/social/$', 'apps.account.views.signup_social'),

    # connect section
    url(r'^connect/fb/$', 'apps.account.views.auth_init', {'mode': 'CONN', 'type': 'FB'}),
    url(r'^connect/tw/$', 'apps.account.views.auth_init', {'mode': 'CONN', 'type': 'TW'}),
    url(r'^connect/kaist/$', 'apps.account.views.auth_init', {'mode': 'CONN', 'type': 'KAIST'}),

    # disconnect section
    url(r'^disconnect/fb/$', 'apps.account.views.disconnect', {'type': 'FB'}),
    url(r'^disconnect/tw/$', 'apps.account.views.disconnect', {'type': 'TW'}),
    url(r'^disconnect/kaist/$', 'apps.account.views.disconnect', {'type': 'KAIST'}),

    # callback section
    url(r'^callback/$', 'apps.account.views.auth_callback'),

    # util section
    url(r'^util/email/check/$', 'apps.account.views.email_check'),
]
