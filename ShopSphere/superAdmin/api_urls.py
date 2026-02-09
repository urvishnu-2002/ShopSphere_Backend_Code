from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    VendorRequestViewSet, VendorManagementViewSet, ProductManagementViewSet, DashboardView
)

router = DefaultRouter()
router.register(r'vendor-requests', VendorRequestViewSet, basename='vendor_request')
router.register(r'vendors', VendorManagementViewSet, basename='vendor_management')
router.register(r'products', ProductManagementViewSet, basename='product_management')

urlpatterns = [
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='admin_dashboard_api'),
    
    # Router endpoints
    path('', include(router.urls)),
]
