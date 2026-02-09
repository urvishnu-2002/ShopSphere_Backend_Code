from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from ecommapp.models import VendorProfile, Product


def is_admin(user):
    """Check if user is a superuser"""
    return user.is_superuser


@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Default admin app dashboard dashboard.
    Shows high-level overview of platform statistics.
    This is the main entry point for the default admin.
    """
    
    # Get statistics
    total_vendors = VendorProfile.objects.count()
    pending_vendors = VendorProfile.objects.filter(approval_status='pending').count()
    approved_vendors = VendorProfile.objects.filter(approval_status='approved').count()
    rejected_vendors = VendorProfile.objects.filter(approval_status='rejected').count()
    blocked_vendors = VendorProfile.objects.filter(is_blocked=True).count()
    
    total_products = Product.objects.count()
    blocked_products = Product.objects.filter(is_blocked=True).count()
    
    # Get recent activities
    recent_vendors = VendorProfile.objects.all().order_by('-created_at')[:5]
    recent_products = Product.objects.all().order_by('-created_at')[:5]

    context = {
        'total_vendors': total_vendors,
        'pending_vendors': pending_vendors,
        'approved_vendors': approved_vendors,
        'rejected_vendors': rejected_vendors,
        'blocked_vendors': blocked_vendors,
        'total_products': total_products,
        'blocked_products': blocked_products,
        'recent_vendors': recent_vendors,
        'recent_products': recent_products,
    }

    return render(request, 'adminapp/dashboard.html', context)


@user_passes_test(is_admin)
def vendor_list(request):
    """
    View all vendors in the system.
    Allows filtering and viewing details.
    """
    
    status_filter = request.GET.get('status', '')
    block_filter = request.GET.get('blocked', '')

    vendors = VendorProfile.objects.all()

    if status_filter:
        vendors = vendors.filter(approval_status=status_filter)

    if block_filter == 'blocked':
        vendors = vendors.filter(is_blocked=True)
    elif block_filter == 'active':
        vendors = vendors.filter(is_blocked=False)

    vendors = vendors.order_by('-created_at')

    context = {
        'vendors': vendors,
        'status_filter': status_filter,
        'block_filter': block_filter,
    }

    return render(request, 'adminapp/vendor_list.html', context)


@user_passes_test(is_admin)
def vendor_details(request, vendor_id):
    """View detailed information about a vendor"""
    
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    products = vendor.products.all()
    approval_logs = vendor.approval_logs.all()

    context = {
        'vendor': vendor,
        'products': products,
        'approval_logs': approval_logs,
    }

    return render(request, 'adminapp/vendor_details.html', context)


@user_passes_test(is_admin)
def product_list(request):
    """View all products in the system"""
    
    block_filter = request.GET.get('blocked', '')
    vendor_filter = request.GET.get('vendor', '')

    products = Product.objects.all().select_related('vendor')

    if block_filter == 'blocked':
        products = products.filter(is_blocked=True)
    elif block_filter == 'active':
        products = products.filter(is_blocked=False)

    if vendor_filter:
        products = products.filter(vendor__id=vendor_filter)

    products = products.order_by('-created_at')

    # Get all vendors for filter dropdown
    vendors = VendorProfile.objects.filter(approval_status='approved').order_by('shop_name')

    context = {
        'products': products,
        'vendors': vendors,
        'block_filter': block_filter,
        'vendor_filter': vendor_filter,
    }

    return render(request, 'adminapp/product_list.html', context)


@user_passes_test(is_admin)
def system_settings(request):
    """
    System settings and configuration page.
    For future expansion - email settings, system configuration, etc.
    """
    
    context = {
        'message': 'System settings page'
    }

    return render(request, 'adminapp/system_settings.html', context)