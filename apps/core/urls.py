from django.conf.urls import url
from django.shortcuts import redirect

urlpatterns = [
    url(r'^$', lambda x: redirect('/account/profile/')),

    # package: auth
    url(r'^login/$', 'apps.core.views.auth.login'),
    url(r'^logout/$', 'apps.core.views.auth.logout'),

    url(r'^auth/email/$', 'apps.core.views.auth.email_resend'),
    url(r'^auth/email/(?P<tokenid>\w+)$', 'apps.core.views.auth.email'),

    url(r'^login/fb/$', 'apps.core.views.auth.init', {'mode': 'LOGIN', 'type': 'FB'}),
    url(r'^login/tw/$', 'apps.core.views.auth.init', {'mode': 'LOGIN', 'type': 'TW'}),
    url(r'^login/kaist/$', 'apps.core.views.auth.init', {'mode': 'LOGIN', 'type': 'KAIST'}),

    url(r'^connect/fb/$', 'apps.core.views.auth.init', {'mode': 'CONN', 'type': 'FB'}),
    url(r'^connect/tw/$', 'apps.core.views.auth.init', {'mode': 'CONN', 'type': 'TW'}),
    url(r'^connect/kaist/$', 'apps.core.views.auth.init', {'mode': 'CONN', 'type': 'KAIST'}),

    url(r'^renew/kaist/$', 'apps.core.views.auth.init', {'mode': 'RENEW', 'type': 'KAIST'}),

    url(r'^callback/$', 'apps.core.views.auth.callback'),


    # package: account
    url(r'^signup/$', 'apps.core.views.account.signup'),
    url(r'^signup/social/$', 'apps.core.views.account.signup', {'is_social': True}),

    url(r'^disconnect/fb/$', 'apps.core.views.account.disconnect', {'type': 'FB'}),
    url(r'^disconnect/tw/$', 'apps.core.views.account.disconnect', {'type': 'TW'}),

    url(r'^deactivate/$', 'apps.core.views.account.deactivate'),


    # package: profile
    url(r'^profile/$', 'apps.core.views.profile.main'),

    url(r'^service/$', 'apps.core.views.profile.service'),

    url(r'^point/$', 'apps.core.views.profile.point'),

    url(r'^unregister/$', 'apps.core.views.profile.unregister'),


    # package: password
    url(r'^password/change/$', 'apps.core.views.password.change'),

    url(r'^password/reset/$', 'apps.core.views.password.reset_email'),
    url(r'^password/reset/(?P<tokenid>\w+)$', 'apps.core.views.password.reset'),
    ]
