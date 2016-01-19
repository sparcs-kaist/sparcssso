from django.conf.urls import url

urlpatterns = [
    # token section
    url(r'^token/require/$', 'apps.api.views.token_require'),
    url(r'^token/info/$', 'apps.api.views.token_info'),

    # point section
    url(r'^point/$', 'apps.api.views.point'),

    # email section
    url(r'^email/$', 'apps.api.views.email'),
]
