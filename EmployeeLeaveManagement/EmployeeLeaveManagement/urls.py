from django.conf.urls import url, include
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from .views import *
from eom.views import eom_view

urlpatterns = [
    url(r'^$', home_view, name='home'),
    url(r'^home/$', home_view, name='home'),
    url(r'^admin/', admin.site.urls),
    url(r'^', include('elm.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^debug/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Admin Site Config
admin.sites.AdminSite.site_header = 'Administration'
admin.sites.AdminSite.site_title = 'Administration'
admin.sites.AdminSite.index_title = 'Pipeline'