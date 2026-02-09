from rest_framework import serializers
from django.contrib.auth.models import User
from .models import VendorProfile, Product


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class VendorProfileSerializer(serializers.ModelSerializer):
    """Serializer for VendorProfile model"""
    user = UserSerializer(read_only=True)
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    business_type_display = serializers.CharField(source='get_business_type_display', read_only=True)
    id_type_display = serializers.CharField(source='get_id_type_display', read_only=True)
    
    class Meta:
        model = VendorProfile
        fields = [
            'id', 'user', 'shop_name', 'shop_description', 'address',
            'business_type', 'business_type_display', 'id_type', 'id_type_display',
            'id_number', 'id_proof_file', 'approval_status', 'approval_status_display',
            'rejection_reason', 'is_blocked', 'blocked_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'approval_status', 'rejection_reason',
            'is_blocked', 'blocked_reason', 'created_at', 'updated_at'
        ]


class VendorRegistrationSerializer(serializers.Serializer):
    """Serializer for vendor shop details submission"""
    shop_name = serializers.CharField(max_length=100)
    shop_description = serializers.CharField()
    address = serializers.CharField()
    business_type = serializers.ChoiceField(choices=['retail', 'wholesale', 'manufacturer', 'service'])
    id_type = serializers.ChoiceField(choices=['gst', 'pan'])
    id_number = serializers.CharField(max_length=50)
    id_proof_file = serializers.FileField()


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    vendor_name = serializers.CharField(source='vendor.shop_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'vendor', 'vendor_name', 'name', 'description', 'price',
            'quantity', 'image', 'status', 'status_display', 'is_blocked',
            'blocked_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'vendor', 'is_blocked', 'blocked_reason', 'created_at', 'updated_at'
        ]


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products"""
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'quantity', 'image', 'status']


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product list view"""
    vendor_name = serializers.CharField(source='vendor.shop_name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'vendor_name', 'price', 'quantity',
            'status', 'is_blocked', 'created_at'
        ]