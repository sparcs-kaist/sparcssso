from django.conf.urls import url

urlpatterns = [
    url(r'^$', 'apps.account.views.profile'),

    # login section
    url(r'^login/$', 'apps.account.views.login_email'),

    url(r'^login/fb/$', 'apps.account.views.fb_auth_init', {'mode': 'login'}),
    url(r'^login/fb/callback/$', 'apps.account.views.login_fb_callback'),
    url(r'^login/tw/$', 'apps.account.views.tw_auth_init', {'mode': 'login'}),
    url(r'^login/tw/callback/$', 'apps.account.views.login_tw_callback'),

    # logout section
    url(r'^logout/$', 'apps.account.views.logout'),

    # signup section
    url(r'^signup/$', 'apps.account.views.signup'),
    url(r'^signup/fb/(?P<userid>\w+)$',
        'apps.account.views.signup_social', {'type': 'FB'}),
    url(r'^signup/tw/(?P<userid>\w+)$',
        'apps.account.views.signup_social', {'type': 'TW'}),
    url(r'^signup/kaist/(?P<userid>\w+)$',
        'apps.account.views.signup_social', {'type': 'KAIST'}),

    # connect section
    url(r'^connect/fb/$', 'apps.account.views.fb_auth_init', {'mode': 'connect'}),
    url(r'^connect/fb/callback/$', 'apps.account.views.connect_fb_callback'),
    url(r'^connect/tw/$', 'apps.account.views.tw_auth_init', {'mode': 'connect'}),
    url(r'^connect/tw/callback/$', 'apps.account.views.connect_tw_callback'),

    # disconnect section
    url(r'^disconnect/fb/$', 'apps.account.views.disconnect', {'type': 'FB'}),
    url(r'^disconnect/tw/$', 'apps.account.views.disconnect', {'type': 'TW'}),
    url(r'^disconnect/kaist/$', 'apps.account.views.disconnect', {'type': 'KAIST'}),

    url(r'^email-check/$', 'apps.account.views.email_check'),

    # email auth section
    url(r'^email-auth/([\w \[\]\.]{40,})$', 'apps.account.views.email_auth'),
    url(r'^email-reauth/$', 'apps.account.views.send_auth_email'),

    url(r'^profile/$', 'apps.account.views.profile'),

    # password section
    url(r'^password/change/$', 'apps.account.views.password_change'),
    url(r'^password/reset/$', 'apps.account.views.send_reset_email'),
    url(r'^password/reset/(?P<token>\w+)$', 'apps.account.views.password_reset'),
]
