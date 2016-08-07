from django.conf.urls import url
from django.shortcuts import redirect
from apps.core.views import auth, account, profile, password

urlpatterns = [
    url(r'^$', lambda x: redirect('/account/profile/')),

    # package: auth
    url(r'^login/$', auth.login),
    url(r'^logout/$', auth.logout),

    url(r'^auth/email/$', auth.email_resend),
    url(r'^auth/email/(?P<tokenid>\w+)$', auth.email),

    url(r'^login/fb/$', auth.init, {'mode': 'LOGIN', 'type': 'FB'}),
    url(r'^login/tw/$', auth.init, {'mode': 'LOGIN', 'type': 'TW'}),
    url(r'^login/kaist/$', auth.init, {'mode': 'LOGIN', 'type': 'KAIST'}),

    url(r'^connect/fb/$', auth.init, {'mode': 'CONN', 'type': 'FB'}),
    url(r'^connect/tw/$', auth.init, {'mode': 'CONN', 'type': 'TW'}),
    url(r'^connect/kaist/$', auth.init, {'mode': 'CONN', 'type': 'KAIST'}),

    url(r'^renew/kaist/$', auth.init, {'mode': 'RENEW', 'type': 'KAIST'}),

    url(r'^callback$', auth.callback),
    url(r'^callback/$', auth.callback),


    # package: account
    url(r'^signup/$', account.signup),
    url(r'^signup/social/$', account.signup, {'is_social': True}),

    url(r'^deactivate/$', account.deactivate),


    # package: profile
    url(r'^profile/$', profile.main),
    url(r'^disconnect/fb/$', profile.disconnect, {'type': 'FB'}),
    url(r'^disconnect/tw/$', profile.disconnect, {'type': 'TW'}),

    url(r'^log/$', profile.log),
    url(r'^point/$', profile.point),
    url(r'^service/$', profile.service),


    # package: password
    url(r'^password/change/$', password.change),
    url(r'^password/reset/$', password.reset_email),
    url(r'^password/reset/(?P<tokenid>\w+)$', password.reset),
]
