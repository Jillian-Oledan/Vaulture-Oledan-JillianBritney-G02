import os
import base64
import hashlib
import secrets

from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 64 * 1024  # 64 MB ~ 65536 KiB
ARGON2_PARALLELISM = 4


#----Derive a 256-bit key-encryption-key from the master password.---------------------
def derive_kek(master_password: str, salt: bytes) -> bytes:
    return hash_secret_raw(
        secret = master_password.encode(),
        salt = salt,
        time_cost = ARGON2_TIME_COST,
        memory_cost = ARGON2_MEMORY_COST,
        parallelism = ARGON2_PARALLELISM,
        hash_len = 32,
        type = Type.ID
    )



#----Generate a random 256-bit data-encryption-key.------------------------------------
def generate_dek() -> bytes:
    return secrets.token_bytes(32)  # 256-bit DEK



#----Encrypt the DEK under KEK. Returns nonce + ciphertext + tag (48 bytes).-----------
def wrap_dek(kek: bytes, dek: bytes) -> bytes:
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(kek)
    return nonce + aesgcm.encrypt(nonce, dek, None) # 12 + 32 + 16 = 60 bytes



#----Recover the DEK from the wrapped blob. Raises on wrong password.
def unwrap_dek(kek: bytes, wrapped: bytes) -> bytes:
    nonce, ciphertext = wrapped[:12], wrapped[12:]
    aesgcm = AESGCM(kek)
    return aesgcm.decrypt(nonce, ciphertext, None)



#----Encrypt a vault entry. Returns nonce + ciphertext + tag (12 + len(ciphertext) bytes).----------------------
def encrypt_entry(dek: bytes, plaintext: str) -> bytes:
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(dek)
    return nonce + aesgcm.encrypt(nonce, plaintext.encode(), None) # 12 + len(ciphertext)



#----Decrypt a vault entry. Raises on wrong DEK.------------------------------------------------
def decrypt_entry(dek: bytes, blob: bytes) -> str:
    nonce, ciphertext = blob[:12], blob[12:]
    aesgcm = AESGCM(dek)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()