from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as drf_views
from .api_views import (
    RegisterView, LoginView, VendorDetailsView, VendorDashboardView,
    VendorProfileDetailView, ProductViewSet, ApprovalStatusView, UserProfileView
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='api_register'),
    path('login/', LoginView.as_view(), name='api_login'),
    path('auth-token/', drf_views.obtain_auth_token, name='api_token_auth'),
    
    # Vendor endpoints
    path('vendor/profile/', VendorProfileDetailView.as_view(), name='vendor_profile'),
    path('vendor/details/', VendorDetailsView.as_view(), name='api_vendor_details'),
    path('vendor/dashboard/', VendorDashboardView.as_view(), name='vendor_dashboard'),
    path('vendor/approval-status/', ApprovalStatusView.as_view(), name='approval_status'),
    
    # User endpoints
    path('user/profile/', UserProfileView.as_view(), name='user_profile'),
    
    # Products
    path('', include(router.urls)),
]