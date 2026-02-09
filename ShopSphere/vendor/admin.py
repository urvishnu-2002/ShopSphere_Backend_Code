from django.contrib import admin
from .models import VendorProfile, Product


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'user', 'approval_status', 'is_blocked', 'created_at')
    list_filter = ('approval_status', 'is_blocked', 'created_at', 'business_type')
    search_fields = ('shop_name', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'price', 'quantity', 'status', 'is_blocked', 'created_at')
    list_filter = ('status', 'is_blocked', 'created_at', 'vendor')
    search_fields = ('name', 'description', 'vendor__shop_name')
    readonly_fields = ('created_at', 'updated_at')