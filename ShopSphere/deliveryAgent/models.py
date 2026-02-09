from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class Agent(AbstractUser):
    mobile = models.CharField(max_length=15, blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    vehicle_type = models.CharField(max_length=20, blank=True, null=True)

    # Overriding these to resolve clashes with default auth.User
    groups = models.ManyToManyField(
        Group,
        related_name="agent_groups", 
        blank=True,
        help_text="The groups this agent belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="agent_permissions",
        blank=True,
        help_text="Specific permissions for this agent.",
        verbose_name="user permissions",
    )

    def __str__(self):
        return self.username