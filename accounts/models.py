from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    ADMIN, MEMBER = "admin", "member"
    ROLES = [(ADMIN, "Admin"), (MEMBER, "Member")]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=[('admin', 'Admin'), ('customer', 'Customer')], default='customer')
    contact_number = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to="profiles/", blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_admin_role(self):
        return self.role == self.ADMIN

    kdf_salt = models.CharField(max_length=64, blank=True)
    master_key_check = models.TextField(blank=True)