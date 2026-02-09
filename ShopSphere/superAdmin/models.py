from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from ecommapp.models import VendorProfile, Product


class VendorApprovalLog(models.Model):
    """
    Log for tracking vendor approval/rejection actions and admin notes.
    Keeps auditable record of admin decisions.
    """
    
    ACTION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('blocked', 'Blocked'),
        ('unblocked', 'Unblocked'),
        ('reviewed', 'Reviewed'),
    ]

    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='approval_logs')
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='vendor_approvals')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.vendor.shop_name} - {self.action} by {self.admin_user.username if self.admin_user else 'System'}"


class ProductApprovalLog(models.Model):
    """
    Log for tracking product blocking/unblocking actions.
    Keeps auditable record of admin decisions on products.
    """
    
    ACTION_CHOICES = [
        ('blocked', 'Blocked'),
        ('unblocked', 'Unblocked'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='approval_logs')
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='product_approvals')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.product.name} - {self.action} by {self.admin_user.username if self.admin_user else 'System'}"
