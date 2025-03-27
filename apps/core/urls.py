from django.conf import settings
from django.shortcuts import redirect
from django.urls import path

from apps.core.views import account, auth, password, profile


urlpatterns = [
    path('', lambda x: redirect('/account/profile/')),

    # package: auth
    path('login/', auth.login),
    path('login/internal/', auth.login_internal),
    path('logout/', auth.logout),

    path('login/fb/', auth.init, {'mode': 'LOGIN', 'site': 'FB'}),
    path('login/tw/', auth.init, {'mode': 'LOGIN', 'site': 'TW'}),

    path('connect/fb/', auth.init, {'mode': 'CONN', 'site': 'FB'}),
    path('connect/tw/', auth.init, {'mode': 'CONN', 'site': 'TW'}),

    path('callback', auth.callback),
    path('callback/', auth.callback),


    # package: account
    path('signup/', account.signup),
    path('signup/social/', account.signup, {'social': True}),

    path('deactivate/', account.deactivate),


    # package: profile
    path('profile/', profile.main),

    path('disconnect/fb/', profile.disconnect, {'site': 'FB'}),
    path('disconnect/tw/', profile.disconnect, {'site': 'TW'}),

    path('email/change/', profile.email),
    path('email/verify/', profile.email_resend),
    path('email/verify/<str:tokenid>/', profile.email_verify),

    path('log/', profile.log),
    path('point/', profile.point),
    path('service/', profile.service),


    # package: password
    path('password/change/', password.change),
    path('password/reset/', password.reset_email),
    path('password/reset/<str:tokenid>/', password.reset),
]


if settings.KAIST_APP_ENABLED:
    urlpatterns += [
        path('login/kaist/', auth.init, {'mode': 'LOGIN', 'site': 'KAIST'}),
        path('connect/kaist/', auth.init, {'mode': 'CONN', 'site': 'KAIST'}),
        path('renew/kaist/', auth.init, {'mode': 'RENEW', 'site': 'KAIST'}),
    ]

