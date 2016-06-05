from django.conf import settings
from django.conf import urls
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from apps.core.views import general

urlpatterns = [
    url(r'^$', general.main),

    url(r'^lang/(?P<code>\w+)', general.lang),

    url(r'^credits/', general.credits),
    url(r'^terms/', general.terms),
    url(r'^privacy/', general.privacy),
    url(r'^stats/', general.stats),
    url(r'^help/', general.help),
    url(r'^doc/dev/', general.doc_dev),
    url(r'^doc/sysop/', general.doc_sysop),

    url(r'^account/', include('apps.core.urls')),
    url(r'^api/', include('apps.api.urls')),
    url(r'^manage/', include(admin.site.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urls.handler400 = lambda r: render(r, 'error/400.html', status=400)
urls.handler403 = lambda r: render(r, 'error/403.html', status=403)
urls.handler404 = lambda r: render(r, 'error/404.html', status=404)
urls.handler500 = lambda r: render(r, 'error/500.html', status=500)

admin.site.site_header = 'SPARCS SSO Administration'
admin.site.site_title = 'SPARCS SSO Admin'
admin.site.index_title = ''
admin.site.login_template = 'account/login.dummy.html'
