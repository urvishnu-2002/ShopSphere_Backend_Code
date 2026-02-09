from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='adminapp_dashboard'),
    path('dashboard/', views.admin_dashboard, name='adminapp_dashboard_alt'),

    # Vendor Management
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/<int:vendor_id>/', views.vendor_details, name='vendor_details'),

    # Product Management
    path('products/', views.product_list, name='product_list'),

    # System Settings
    path('settings/', views.system_settings, name='system_settings'),
]