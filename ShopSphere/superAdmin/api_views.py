from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.contrib.auth.models import User
from django.db.models import Q
from ecommapp.models import VendorProfile, Product
from .models import VendorApprovalLog, ProductApprovalLog
from .serializers import (
    VendorApprovalLogSerializer, ProductApprovalLogSerializer,
    AdminVendorDetailSerializer, AdminProductDetailSerializer,
    AdminVendorListSerializer, AdminProductListSerializer,
    ApproveVendorSerializer, RejectVendorSerializer,
    BlockVendorSerializer, UnblockVendorSerializer,
    BlockProductSerializer, UnblockProductSerializer
)


class AdminLoginRequiredMixin:
    """Ensure user is admin"""
    permission_classes = [IsAuthenticated, IsAdminUser]


class VendorRequestViewSet(AdminLoginRequiredMixin, viewsets.ModelViewSet):
    """Manage vendor approval requests"""
    queryset = VendorProfile.objects.filter(approval_status='pending')
    serializer_class = AdminVendorDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def list(self, request, *args, **kwargs):
        queryset = VendorProfile.objects.filter(approval_status='pending')
        
        # Search by shop name or owner email
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(shop_name__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        serializer = AdminVendorDetailSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a vendor"""
        vendor = self.get_object()
        
        if vendor.approval_status != 'pending':
            return Response({
                'error': 'Only pending vendors can be approved'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ApproveVendorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update vendor status
        vendor.approval_status = 'approved'
        vendor.save()
        
        # Log the action
        VendorApprovalLog.objects.create(
            vendor=vendor,
            admin_user=request.user,
            action='approved',
            reason=serializer.validated_data.get('reason', '')
        )
        
        return Response({
            'message': 'Vendor approved successfully',
            'vendor': AdminVendorDetailSerializer(vendor).data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a vendor"""
        vendor = self.get_object()
        
        if vendor.approval_status != 'pending':
            return Response({
                'error': 'Only pending vendors can be rejected'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = RejectVendorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update vendor status
        vendor.approval_status = 'rejected'
        vendor.rejection_reason = serializer.validated_data['reason']
        vendor.save()
        
        # Log the action
        VendorApprovalLog.objects.create(
            vendor=vendor,
            admin_user=request.user,
            action='rejected',
            reason=serializer.validated_data['reason']
        )
        
        return Response({
            'message': 'Vendor rejected successfully',
            'vendor': AdminVendorDetailSerializer(vendor).data
        })


class VendorManagementViewSet(AdminLoginRequiredMixin, viewsets.ModelViewSet):
    """Manage all vendors"""
    queryset = VendorProfile.objects.exclude(approval_status='pending')
    serializer_class = AdminVendorListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def list(self, request, *args, **kwargs):
        queryset = VendorProfile.objects.all()
        
        # Filter by status
        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(approval_status=status_filter)
        
        # Search by shop name or owner email
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(shop_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        # Filter by blocked status
        blocked_filter = request.query_params.get('blocked', None)
        if blocked_filter == 'true':
            queryset = queryset.filter(is_blocked=True)
        elif blocked_filter == 'false':
            queryset = queryset.filter(is_blocked=False)
        
        serializer = AdminVendorListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Get detailed vendor information"""
        vendor = self.get_object()
        serializer = AdminVendorDetailSerializer(vendor)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """Block a vendor"""
        vendor = self.get_object()
        
        serializer = BlockVendorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        vendor.is_blocked = True
        vendor.blocked_reason = serializer.validated_data['reason']
        vendor.save()
        
        # Block all vendor's products
        Product.objects.filter(vendor=vendor).update(is_blocked=True)
        
        # Log the action
        VendorApprovalLog.objects.create(
            vendor=vendor,
            admin_user=request.user,
            action='blocked',
            reason=serializer.validated_data['reason']
        )
        
        return Response({
            'message': 'Vendor blocked successfully',
            'vendor': AdminVendorDetailSerializer(vendor).data
        })
    
    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        """Unblock a vendor"""
        vendor = self.get_object()
        
        serializer = UnblockVendorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        vendor.is_blocked = False
        vendor.blocked_reason = ''
        vendor.save()
        
        # Log the action
        VendorApprovalLog.objects.create(
            vendor=vendor,
            admin_user=request.user,
            action='unblocked',
            reason=serializer.validated_data.get('reason', '')
        )
        
        return Response({
            'message': 'Vendor unblocked successfully',
            'vendor': AdminVendorDetailSerializer(vendor).data
        })


class ProductManagementViewSet(AdminLoginRequiredMixin, viewsets.ModelViewSet):
    """Manage all products"""
    queryset = Product.objects.all()
    serializer_class = AdminProductListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def list(self, request, *args, **kwargs):
        queryset = Product.objects.all()
        
        # Filter by status
        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by blocked status
        blocked_filter = request.query_params.get('blocked', None)
        if blocked_filter == 'true':
            queryset = queryset.filter(is_blocked=True)
        elif blocked_filter == 'false':
            queryset = queryset.filter(is_blocked=False)
        
        # Search by product name
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(vendor__shop_name__icontains=search)
            )
        
        # Filter by vendor
        vendor_id = request.query_params.get('vendor_id', None)
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
        
        serializer = AdminProductListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Get detailed product information"""
        product = self.get_object()
        serializer = AdminProductDetailSerializer(product)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """Block a product"""
        product = self.get_object()
        
        serializer = BlockProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product.is_blocked = True
        product.blocked_reason = serializer.validated_data['reason']
        product.save()
        
        # Log the action
        ProductApprovalLog.objects.create(
            product=product,
            admin_user=request.user,
            action='blocked',
            reason=serializer.validated_data['reason']
        )
        
        return Response({
            'message': 'Product blocked successfully',
            'product': AdminProductDetailSerializer(product).data
        })
    
    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        """Unblock a product"""
        product = self.get_object()
        
        serializer = UnblockProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product.is_blocked = False
        product.blocked_reason = ''
        product.save()
        
        # Log the action
        ProductApprovalLog.objects.create(
            product=product,
            admin_user=request.user,
            action='unblocked',
            reason=serializer.validated_data.get('reason', '')
        )
        
        return Response({
            'message': 'Product unblocked successfully',
            'product': AdminProductDetailSerializer(product).data
        })


class DashboardView(AdminLoginRequiredMixin, generics.GenericAPIView):
    """Admin dashboard statistics"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        total_vendors = VendorProfile.objects.count()
        pending_vendors = VendorProfile.objects.filter(approval_status='pending').count()
        approved_vendors = VendorProfile.objects.filter(approval_status='approved').count()
        blocked_vendors = VendorProfile.objects.filter(is_blocked=True).count()
        
        total_products = Product.objects.count()
        pending_products = Product.objects.filter(status='pending').count()
        approved_products = Product.objects.filter(status='approved').count()
        blocked_products = Product.objects.filter(is_blocked=True).count()
        
        return Response({
            'vendors': {
                'total': total_vendors,
                'pending': pending_vendors,
                'approved': approved_vendors,
                'blocked': blocked_vendors
            },
            'products': {
                'total': total_products,
                'pending': pending_products,
                'approved': approved_products,
                'blocked': blocked_products
            }
        })
