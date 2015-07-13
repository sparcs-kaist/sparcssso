from django.conf.urls import url

urlpatterns = [
    url(r'^$', 'apps.account.views.main'),
    url(r'^login/$', 'apps.account.views.login_email'),
    url(r'^login/facebook/$', 'apps.account.views.login_fb'),
    url(r'^login/facebook/callback/$', 'apps.account.views.login_fb_callback'),
    url(r'^logout/$', 'apps.account.views.logout'),
    url(r'^signup/$', 'apps.account.views.signup'),
    url(r'^email-check/$', 'apps.account.views.email_check'),
    url(r'^profile/$', 'apps.account.views.profile'),
    url(r'^changepw/$', 'apps.account.views.changepw'),
]
