from django.conf import settings
from django.db import models

class VaultEntry(models.Model):
    TYPES = [("login", "Login"), ("note", "Secure note")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="vault_entries")
    title = models.CharField(max_length=100)
    entry_type = models.CharField(max_length=20, choices=TYPES, default="login")
    encrypted_data = models.TextField()   # AES-GCM ciphertext from the browser
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]