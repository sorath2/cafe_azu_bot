from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('azucafe.urls')),
    path('azucafe/admin/', admin.site.urls),
]

handler404 = 'azucafe.views_error.page_not_found'
handler403 = 'azucafe.views_error.permission_denied'
handler500 = 'azucafe.views_error.server_error'

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
