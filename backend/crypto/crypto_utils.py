import hashlib
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pqcrypto.kem import ml_kem_512

MAGIC = b"STEG"

def derive_aes_key(shared_secret: bytes) -> bytes:
    return hashlib.sha256(shared_secret).digest()

def aes_encrypt(data: bytes, key: bytes):
    aes = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ciphertext = aes.encrypt(nonce, data, None)
    return nonce, ciphertext

def aes_decrypt(nonce: bytes, ciphertext: bytes, key: bytes):
    aes = AESGCM(key)
    return aes.decrypt(nonce, ciphertext, None)

def kyber_encapsulate(public_key: bytes):
    return ml_kem_512.encrypt(public_key)

def kyber_decapsulate(private_key: bytes, ciphertext: bytes):
    return ml_kem_512.decrypt(private_key, ciphertext)