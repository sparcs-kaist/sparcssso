from django.conf import settings, urls
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path, re_path

from apps.core.views import general


urlpatterns = [
    path('', general.main),

    path('lang/<str:code>/', general.lang),

    re_path(r'^terms/(?P<version>[\d\.]+)?$', general.terms),
    re_path(r'^privacy/(?P<version>[\d\.]+)?$', general.privacy),

    path('credits/', general.credits),
    path('stats/', general.stats),
    path('help/', general.help),
    path('contact/', general.contact),

    path('account/', include('apps.core.urls')),
    path('api/', include('apps.api.urls')),
    path('dev/', include('apps.dev.urls')),

    path('manage/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

urls.handler400 = lambda r: render(r, 'error/400.html', status=400)
urls.handler403 = lambda r: render(r, 'error/403.html', status=403)
urls.handler404 = lambda r: render(r, 'error/404.html', status=404)
urls.handler500 = lambda r: render(r, 'error/500.html', status=500)

admin.site.site_header = 'SPARCS SSO Administration'
admin.site.site_title = 'SPARCS SSO Admin'
admin.site.index_title = ''
admin.site.login_template = 'account/login/dummy.html'
