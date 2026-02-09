from django.shortcuts import render

# Create your views here.
import random
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse
from .models import VendorProfile, Product


# ============================================================================
# AUTHENTICATION VIEWS - VENDOR REGISTRATION AND LOGIN
# ============================================================================

def register_view(request):
    """Vendor registration - creates user account and sends OTP"""
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password') 

        # Validation
        if password != confirm_password:
            return render(request, 'ecommapp/register.html', {
                'error': 'Passwords do not match'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'ecommapp/register.html', {
                'error': 'Username already exists'
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'ecommapp/register.html', {
                'error': 'Email already exists'
            })

        # Generate OTP
        otp = random.randint(100000, 999999)

        # Store in session
        request.session['reg_data'] = {
            'username': username,
            'email': email,
            'password': password,
            'otp': otp
        }

        # Send OTP email
        try:
            send_mail(
                subject="Your Vendor OTP",
                message=f"Your OTP for registration is: {otp}\n\nDo not share this OTP with anyone.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
            )
        except Exception as e:
            return render(request, 'ecommapp/register.html', {
                'error': f'Error sending OTP: {str(e)}'
            })

        return redirect('verify_otp')

    return render(request, 'ecommapp/register.html')


def verify_otp_view(request):
    """Verify OTP and create user account"""
    if request.method == "POST":
        entered_otp = request.POST.get('otp')
        reg_data = request.session.get('reg_data')

        if not reg_data:
            return render(request, 'ecommapp/verify_otp.html', {
                'error': 'Session expired. Please register again.'
            })

        if str(reg_data['otp']) == entered_otp:
            # Create user
            user = User.objects.create_user(
                username=reg_data['username'],
                email=reg_data['email'],
                password=reg_data['password']

            )
            request.session['vendor_user_id'] = user.id
            del request.session['reg_data']
            # if request.accessed_from_mobile:
            #     return JsonResponse({'success': True, 'message': 'OTP verified. Please complete your vendor details.'})

            return redirect('vendor_details')
        else:
            return render(request, 'ecommapp/verify_otp.html', {
                'error': 'Invalid OTP. Please try again.'
            })

    return render(request, 'ecommapp/verify_otp.html')


def vendor_details_view(request):
    """Vendor submits shop details to complete registration"""
    user_id = request.session.get('vendor_user_id')
    
    if not user_id:
        return redirect('register')

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        VendorProfile.objects.create(
            user=user,
            shop_name=request.POST.get('shop_name'),
            shop_description=request.POST.get('shop_description'),
            address=request.POST.get('address'),
            business_type=request.POST.get('business_type'),
            id_type=request.POST.get('id_type'),
            id_number=request.POST.get('id_number'),
            id_proof_file=request.FILES.get('id_proof_file'),
            approval_status='pending'  # Status defaults to pending
        )
        if 'vendor_user_id' in request.session:
            del request.session['vendor_user_id']
        return redirect('login')

    return render(request, 'ecommapp/vendor_details.html')


def login_view(request):
    """Vendor login"""
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('vendor_home')
        else:
            return render(request, 'ecommapp/login.html', {
                'error': 'Invalid credentials'
            })

    return render(request, 'ecommapp/login.html')


def logout_view(request):
    """Vendor logout"""
    logout(request)
    return redirect('login')


# ============================================================================
# VENDOR DASHBOARD - APPROVAL STATUS AND PRODUCT MANAGEMENT
# ============================================================================

@login_required(login_url='login')
def vendor_home_view(request):
    """
    Vendor home page with approval status.
    If not approved, show status (pending/rejected).
    If approved, show vendor dashboard.
    """
    try:
        vendor = request.user.vendor_profile
    except VendorProfile.DoesNotExist:
        return redirect('login')

    # Check if vendor is blocked
    if vendor.is_blocked:
        return render(request, 'ecommapp/vendor_blocked.html', {
            'vendor': vendor
        })

    # If not approved, show status page
    if vendor.approval_status != 'approved':
        return render(request, 'ecommapp/approval_status.html', {
            'vendor': vendor,
            'status': vendor.approval_status,
            'rejection_reason': vendor.rejection_reason
        })

    # If approved, show products dashboard
    products = vendor.products.all()
    return render(request, 'ecommapp/vendor_dashboard.html', {
        'vendor': vendor,
        'products': products
    })


@login_required(login_url='login')
def approval_status_view(request):
    """
    Show approval status page.
    Accessible only when not approved.
    """
    try:
        vendor = request.user.vendor_profile
    except VendorProfile.DoesNotExist:
        return redirect('login')

    if vendor.approval_status == 'approved':
        return redirect('vendor_home')

    return render(request, 'ecommapp/approval_status.html', {
        'vendor': vendor,
        'status': vendor.approval_status,
        'rejection_reason': vendor.rejection_reason
    })


# ============================================================================
# PRODUCT MANAGEMENT - VENDOR SIDE
# ============================================================================

@login_required(login_url='login')
def add_product_view(request):
    """Add new product to vendor's store"""
    try:
        vendor = request.user.vendor_profile
    except VendorProfile.DoesNotExist:
        return redirect('login')

    # Check approval
    if vendor.approval_status != 'approved':
        return redirect('approval_status')

    if request.method == "POST":
        Product.objects.create(
            vendor=vendor,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            price=request.POST.get('price'),
            quantity=request.POST.get('quantity'),
            image=request.FILES.get('image'),
            status='active'
        )
        return redirect('vendor_home')

    return render(request, 'ecommapp/add_product.html', {
        'vendor': vendor
    })


@login_required(login_url='login')
def edit_product_view(request, product_id):
    """Edit product details"""
    try:
        vendor = request.user.vendor_profile
    except VendorProfile.DoesNotExist:
        return redirect('login')

    if vendor.approval_status != 'approved':
        return redirect('approval_status')

    product = get_object_or_404(Product, id=product_id, vendor=vendor)

    if request.method == "POST":
        product.name = request.POST.get('name', product.name)
        product.description = request.POST.get('description', product.description)
        product.price = request.POST.get('price', product.price)
        product.quantity = request.POST.get('quantity', product.quantity)
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        product.save()
        return redirect('vendor_home')

    return render(request, 'ecommapp/edit_product.html', {
        'vendor': vendor,
        'product': product
    })


@login_required(login_url='login')
def delete_product_view(request, product_id):
    """Delete product"""
    try:
        vendor = request.user.vendor_profile
    except VendorProfile.DoesNotExist:
        return redirect('login')

    if vendor.approval_status != 'approved':
        return redirect('approval_status')

    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    product.delete()
    return redirect('vendor_home')


@login_required(login_url='login')
def view_product_view(request, product_id):
    """View product details"""
    try:
        vendor = request.user.vendor_profile
    except VendorProfile.DoesNotExist:
        return redirect('login')

    product = get_object_or_404(Product, id=product_id, vendor=vendor)

    context = {
        'vendor': vendor,
        'product': product,
        'is_blocked': product.is_blocked,
        'blocked_reason': product.blocked_reason
    }

    return render(request, 'ecommapp/product_detail.html', context)