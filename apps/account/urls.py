from django.conf.urls import url

urlpatterns = [
    url(r'^$', 'apps.account.views.main'),

    url(r'^login/$', 'apps.account.views.login_email'),

    url(r'^login/fb/$', 'apps.account.views.login_fb'),
    url(r'^login/fb/callback/$', 'apps.account.views.login_fb_callback'),

    url(r'^login/tw/$', 'apps.account.views.login_tw'),
    url(r'^login/tw/callback/$', 'apps.account.views.login_tw_callback'),

    url(r'^logout/$', 'apps.account.views.logout'),

    url(r'^signup/$', 'apps.account.views.signup'),
    url(r'^signup/social/$', 'apps.account.views.signup_social'),

    url(r'^email-check/$', 'apps.account.views.email_check'),

    url(r'^email-auth/([\w \[\]\.]{40,})/$', 'apps.account.views.email_auth'),

    url(r'^profile/$', 'apps.account.views.profile'),

    url(r'^password/change/$', 'apps.account.views.password_change'),
    url(r'^password/reset/$', 'apps.account.views.password_reset'),
]
