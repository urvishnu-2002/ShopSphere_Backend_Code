from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('', include('user.urls')),
    path('admin-panel/', include('adminapp.urls')),
    path('main/', include('mainApp.urls')),
    
    # API endpoints
    path('api/vendor/', include('ecommapp.api_urls')),
    path('api/admin/', include('mainApp.api_urls')),
    path('api/auth/', include('rest_framework.urls')),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
