from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail import urls as wagtail_urls

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('cms/', include(wagtailadmin_urls)),  # Adjusted Wagtail admin URL
    path('documents/', include(wagtaildocs_urls)), 
    path('accounts/', include('allauth.urls')),
    path('assessment/', include('assessment.urls')),
    path('roadmap/', include('roadmap.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('', TemplateView.as_view(template_name='core/home.html'), name='home'),
    path('', include(wagtail_urls)), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
    