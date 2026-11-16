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
    kdf_salt = models.CharField(max_length=64, blank=True)
    master_key_check = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_admin_role(self):
        return self.role == self.ADMIN

class VaultEntry(models.Model):
    TYPES = [("login", "Login"), ("note", "Secure note")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vault_entries")
    title = models.CharField(max_length=100)
    entry_type = models.CharField(max_length=20, choices=TYPES, default="login")
    encrypted_data = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]