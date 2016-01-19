from django.conf import settings
from django.conf.urls import include, url, \
    handler400, handler403, handler404, handler500
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render

urlpatterns = [
    url(r'^$', 'apps.core.views.general.main'),

    url(r'^lang/(?P<code>\w+)', 'apps.core.views.general.lang'),

    url(r'^credits/', 'apps.core.views.general.credits'),
    url(r'^terms/', 'apps.core.views.general.terms'),
    url(r'^privacy/', 'apps.core.views.general.privacy'),

    url(r'^doc/dev/', 'apps.core.views.general.doc_dev'),
    url(r'^doc/sysop/', 'apps.core.views.general.doc_sysop'),

    url(r'^manage/', include(admin.site.urls)),
    url(r'^account/', include('apps.core.urls')),
    url(r'^api/', include('apps.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = lambda request: render(request, 'error/400.html')
handler403 = lambda request: render(request, 'error/403.html')
handler404 = lambda request: render(request, 'error/404.html')
handler500 = lambda request: render(request, 'error/500.html')
