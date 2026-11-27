import os

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

from accounts.crypto import generate_dek, derive_kek, unwrap_dek, wrap_dek

class User(AbstractUser):
    ADMIN, CUSTOMER = "admin", "customer"
    ROLES = [(ADMIN, "Admin"), (CUSTOMER, "Customer")]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLES, default=CUSTOMER)
    contact_number = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to="profiles/", blank=True, null=True)

    # Master key material
    kdf_salt = models.CharField(max_length=64, blank=True)
    master_key_check = models.BinaryField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.ADMIN
        super().save(*args, **kwargs)

    #---- Master key management methods -------------------------------------------------------

    def set_master_key_material(self, master_password: str):
        salt = os.urandom(16)
        kek = derive_kek(master_password, salt)
        dek = generate_dek()
        
        self.kdf_salt = salt.hex()
        self.master_key_check = wrap_dek(kek, dek)
        self.save()

    def verify_master_key(self, master_password: str) -> bool:
        try:
            kek = derive_kek(master_password, bytes.fromhex(self.kdf_salt))
            unwrap_dek(kek, self.master_key_check)
            return True
        except Exception:
            return False

    def unlock(self, master_password: str) -> bytes:
        kek = derive_kek(master_password, bytes.fromhex(self.kdf_salt))
        return unwrap_dek(kek, self.master_key_check)

    def change_master_key(self, old_password: str, new_password: str):
        dek = self.unlock(old_password)
        salt = os.urandom(16)
        kek = derive_kek(new_password, salt)

        self.kdf_salt = salt.hex()
        self.master_key_check = wrap_dek(kek, dek)
        self.save()
    
    #-----------------------------------------------------------------------------------------------

    @property
    def is_admin_role(self):
        return self.role == self.ADMIN

class VaultEntry(models.Model):
    TYPES = [("login", "Login"), ("note", "Secure note")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vault_entries")
    title = models.CharField(max_length=100)
    entry_type = models.CharField(max_length=20, choices=TYPES, default="login")
    encrypted_data = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]