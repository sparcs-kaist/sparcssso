from django.conf.urls import url

urlpatterns = [
    url(r'^$', 'apps.session.views.main'),
    url(r'^login/$', 'apps.session.views.login'),
    url(r'^logout/$', 'apps.session.views.logout'),
    url(r'^signup/$', 'apps.session.views.signup'),
    url(r'^email-check/$', 'apps.session.views.email_check'),
    url(r'^profile/$', 'apps.session.views.profile'),
    url(r'^changepw/$', 'apps.session.views.changepw'),
]
