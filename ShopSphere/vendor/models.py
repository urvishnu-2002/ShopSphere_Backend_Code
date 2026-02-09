from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class VendorProfile(models.Model):
    """Vendor Profile Model for vendor registration and management"""
    
    BUSINESS_CHOICES = [
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
        ('manufacturer', 'Manufacturer'),
        ('service', 'Service'),
    ]

    ID_PROOF_CHOICES = [
        ('gst', 'GST'),
        ('pan', 'PAN'),
    ]
    
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    shop_name = models.CharField(max_length=100)
    shop_description = models.TextField()
    address = models.TextField()
    business_type = models.CharField(max_length=20, choices=BUSINESS_CHOICES)
    
    # Legacy fields (kept for backward compatibility)
    id_type = models.CharField(max_length=10, choices=ID_PROOF_CHOICES, blank=True, null=True)
    id_number = models.CharField(max_length=50, blank=True, null=True)
    id_proof_file = models.FileField(upload_to='vendor_docs/', blank=True, null=True)
    
    # New GST/PAN fields
    gst_number = models.CharField(max_length=15, blank=True, null=True, help_text="15-digit GST number")
    pan_number = models.CharField(max_length=10, blank=True, null=True, help_text="10-character PAN number")
    pan_name = models.CharField(max_length=100, blank=True, null=True, help_text="Name as per PAN card")
    pan_card_file = models.FileField(upload_to='pan_cards/', blank=True, null=True, help_text="Upload PAN card image")
    
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_blocked = models.BooleanField(default=False)
    blocked_reason = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.shop_name} ({self.user.username})"
    
    @property
    def is_approved(self):
        """Property for backward compatibility"""
        return self.approval_status == 'approved'


class Product(models.Model):
    """Product Model for vendor products"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_blocked = models.BooleanField(default=False)
    blocked_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.vendor.shop_name}"