from rest_framework import serializers
from django.contrib.auth.models import User
from ecommapp.models import VendorProfile, Product
from .models import VendorApprovalLog, ProductApprovalLog


class VendorApprovalLogSerializer(serializers.ModelSerializer):
    """Serializer for VendorApprovalLog model"""
    admin_user_name = serializers.CharField(source='admin_user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = VendorApprovalLog
        fields = [
            'id', 'vendor', 'admin_user', 'admin_user_name', 'action',
            'action_display', 'reason', 'timestamp'
        ]
        read_only_fields = ['id', 'admin_user', 'timestamp']


class ProductApprovalLogSerializer(serializers.ModelSerializer):
    """Serializer for ProductApprovalLog model"""
    admin_user_name = serializers.CharField(source='admin_user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = ProductApprovalLog
        fields = [
            'id', 'product', 'admin_user', 'admin_user_name', 'action',
            'action_display', 'reason', 'timestamp'
        ]
        read_only_fields = ['id', 'admin_user', 'timestamp']


class AdminVendorDetailSerializer(serializers.ModelSerializer):
    """Serializer for admin vendor details view"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    approval_logs = VendorApprovalLogSerializer(source='approval_logs.all', many=True, read_only=True)
    
    class Meta:
        model = VendorProfile
        fields = [
            'id', 'user_username', 'user_email', 'shop_name', 'shop_description',
            'address', 'business_type', 'id_type', 'id_number',
            'approval_status', 'approval_status_display', 'rejection_reason',
            'is_blocked', 'blocked_reason', 'created_at', 'approval_logs'
        ]


class AdminProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for admin product details view"""
    vendor_shop_name = serializers.CharField(source='vendor.shop_name', read_only=True)
    vendor_owner = serializers.CharField(source='vendor.user.username', read_only=True)
    approval_logs = ProductApprovalLogSerializer(source='approval_logs.all', many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'vendor', 'vendor_shop_name', 'vendor_owner', 'name',
            'description', 'price', 'quantity', 'image', 'status',
            'is_blocked', 'blocked_reason', 'created_at', 'approval_logs'
        ]


class AdminVendorListSerializer(serializers.ModelSerializer):
    """Serializer for admin vendor list view"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    
    class Meta:
        model = VendorProfile
        fields = [
            'id', 'shop_name', 'user_email', 'approval_status',
            'approval_status_display', 'is_blocked', 'created_at'
        ]


class AdminProductListSerializer(serializers.ModelSerializer):
    """Serializer for admin product list view"""
    vendor_name = serializers.CharField(source='vendor.shop_name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'vendor', 'vendor_name', 'price', 'quantity',
            'is_blocked', 'created_at'
        ]


class ApproveVendorSerializer(serializers.Serializer):
    """Serializer for approving vendor"""
    reason = serializers.CharField(required=False, allow_blank=True)


class RejectVendorSerializer(serializers.Serializer):
    """Serializer for rejecting vendor"""
    reason = serializers.CharField()


class BlockVendorSerializer(serializers.Serializer):
    """Serializer for blocking vendor"""
    reason = serializers.CharField()


class UnblockVendorSerializer(serializers.Serializer):
    """Serializer for unblocking vendor"""
    reason = serializers.CharField(required=False, allow_blank=True)


class BlockProductSerializer(serializers.Serializer):
    """Serializer for blocking product"""
    reason = serializers.CharField()


class UnblockProductSerializer(serializers.Serializer):
    """Serializer for unblocking product"""
    reason = serializers.CharField(required=False, allow_blank=True)
