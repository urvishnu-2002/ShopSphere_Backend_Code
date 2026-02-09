from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from .models import VendorProfile, Product
from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    VendorProfileSerializer, VendorRegistrationSerializer,
    ProductSerializer, ProductCreateUpdateSerializer, ProductListSerializer
)


class RegisterView(generics.CreateAPIView):
    """Vendor registration endpoint"""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'message': 'User registered successfully',
            'user_id': user.id,
            'username': user.username,
            'email': user.email
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """Vendor login endpoint"""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        
        if user is None:
            return Response({
                'error': 'Invalid username or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        
        # Check if vendor profile exists
        vendor = VendorProfile.objects.filter(user=user).first()
        
        return Response({
            'message': 'Login successful',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'vendor': {
                'id': vendor.id,
                'status': vendor.approval_status,
                'is_blocked': vendor.is_blocked
            } if vendor else None
        }, status=status.HTTP_200_OK)


class VendorDetailsView(generics.GenericAPIView):
    """Submit vendor shop details - Returns HTML page"""
    permission_classes = [AllowAny]  # Allow access for new vendors during registration
    serializer_class = VendorRegistrationSerializer
    
    def get(self, request, *args, **kwargs):
        """Render HTML form for vendor details"""
        from django.shortcuts import render, redirect
        
        # Check if user is coming from registration (has vendor_user_id in session)
        vendor_user_id = request.session.get('vendor_user_id')
        if not vendor_user_id:
            # If authenticated via API token, use that user
            if request.user.is_authenticated:
                return render(request, 'ecommapp/vendor_details.html')
            else:
                return redirect('register')
        
        return render(request, 'ecommapp/vendor_details.html')
    
    def post(self, request, *args, **kwargs):
        """Process vendor details form submission"""
        from django.shortcuts import redirect, render, get_object_or_404
        
        # Get user from session or from authenticated request
        vendor_user_id = request.session.get('vendor_user_id')
        if vendor_user_id:
            user = get_object_or_404(User, id=vendor_user_id)
        elif request.user.is_authenticated:
            user = request.user
        else:
            return redirect('register')
        
        # Check if vendor profile already exists
        vendor = VendorProfile.objects.filter(user=user).first()
        
        if vendor:
            return render(request, 'ecommapp/vendor_details.html', {
                'error': 'Vendor profile already exists'
            })
        
        # Create vendor profile from form data
        VendorProfile.objects.create(
            user=user,
            shop_name=request.POST.get('shop_name'),
            shop_description=request.POST.get('shop_description'),
            address=request.POST.get('address'),
            business_type=request.POST.get('business_type'),
            id_type=request.POST.get('id_type'),
            id_number=request.POST.get('id_number'),
            id_proof_file=request.FILES.get('id_proof_file'),
            approval_status='pending'
        )
        
        # Clear session data
        if 'vendor_user_id' in request.session:
            del request.session['vendor_user_id']
        
        # Redirect to login after successful submission
        return redirect('login')


class VendorDashboardView(generics.RetrieveAPIView):
    """Get vendor dashboard information"""
    permission_classes = [IsAuthenticated]
    serializer_class = VendorProfileSerializer
    
    def get_object(self):
        return VendorProfile.objects.get(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        try:
            vendor = self.get_object()
        except VendorProfile.DoesNotExist:
            return Response({
                'error': 'Vendor profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        products = Product.objects.filter(vendor=vendor)
        
        return Response({
            'vendor': VendorProfileSerializer(vendor).data,
            'products_count': products.count(),
            'approved_products': products.filter(status='approved').count(),
            'pending_products': products.filter(status='pending').count(),
            'blocked_products': products.filter(is_blocked=True).count(),
        }, status=status.HTTP_200_OK)


class VendorProfileDetailView(generics.RetrieveUpdateAPIView):
    """Get or update vendor profile"""
    permission_classes = [IsAuthenticated]
    serializer_class = VendorProfileSerializer
    
    def get_object(self):
        return VendorProfile.objects.get(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        try:
            vendor = self.get_object()
            return Response(VendorProfileSerializer(vendor).data)
        except VendorProfile.DoesNotExist:
            return Response({
                'error': 'Vendor profile not found'
            }, status=status.HTTP_404_NOT_FOUND)


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD operations for products"""
    permission_classes = [IsAuthenticated]
    queryset = Product.objects.all()
    
    def get_queryset(self):
        try:
            vendor = VendorProfile.objects.get(user=self.request.user)
            return Product.objects.filter(vendor=vendor)
        except VendorProfile.DoesNotExist:
            return Product.objects.none()
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        elif self.action == 'list':
            return ProductListSerializer
        return ProductSerializer
    
    def create(self, request, *args, **kwargs):
        try:
            vendor = VendorProfile.objects.get(user=request.user)
        except VendorProfile.DoesNotExist:
            return Response({
                'error': 'Vendor profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product = Product.objects.create(
            vendor=vendor,
            **serializer.validated_data
        )
        
        return Response(
            ProductSerializer(product).data,
            status=status.HTTP_201_CREATED
        )
    
    def list(self, request, *args, **kwargs):
        try:
            vendor = VendorProfile.objects.get(user=request.user)
        except VendorProfile.DoesNotExist:
            return Response({
                'error': 'Vendor profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        queryset = self.get_queryset()
        
        # Filter by status if provided
        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Search by name or description
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        
        if product.vendor.user != request.user:
            return Response({
                'error': 'You do not have permission to delete this product'
            }, status=status.HTTP_403_FORBIDDEN)
        
        product.delete()
        return Response({
            'message': 'Product deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def approved(self, request):
        """Get only approved products"""
        queryset = self.get_queryset().filter(status='approved')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get only pending products"""
        queryset = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def blocked(self, request):
        """Get only blocked products"""
        queryset = self.get_queryset().filter(is_blocked=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ApprovalStatusView(generics.RetrieveAPIView):
    """Get vendor approval status"""
    permission_classes = [IsAuthenticated]
    serializer_class = VendorProfileSerializer
    
    def get_object(self):
        return VendorProfile.objects.get(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        try:
            vendor = self.get_object()
            return Response({
                'approval_status': vendor.approval_status,
                'is_blocked': vendor.is_blocked,
                'rejection_reason': vendor.rejection_reason,
                'blocked_reason': vendor.blocked_reason
            })
        except VendorProfile.DoesNotExist:
            return Response({
                'error': 'Vendor profile not found'
            }, status=status.HTTP_404_NOT_FOUND)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get or update current user profile"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user