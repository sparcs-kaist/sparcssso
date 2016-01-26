from django.conf.urls import url
from apps.api import views

urlpatterns = [
    # token section
    url(r'^token/require/$', views.token_require),
    url(r'^token/info/$', views.token_info),

    # point section
    url(r'^point/$', views.point),

    # email section
    url(r'^email/$', views.email),
]
