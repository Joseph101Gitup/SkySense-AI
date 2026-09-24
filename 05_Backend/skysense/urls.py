"""
URL configuration for SkySenseWeb project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', accounts_views.login_view, name='login'),
    path('register/', accounts_views.register_view, name='register'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('profile/', accounts_views.profile_view, name='profile'),
    path('', include('core.urls', namespace='core')),
    path('', include('predictions.urls', namespace='predictions')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # In production, Nginx/Caddy should serve /media/ directly.
    # The following is a fallback for single-node deployments without a reverse proxy.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
