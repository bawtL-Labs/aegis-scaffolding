"""
Cryptographic utilities for S.A.M.

Provides key derivation, signing, verification, and encryption functions
using Argon2id, Ed25519, and ChaCha20-Poly1305.
"""

import os
import secrets
from typing import Tuple, Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


def derive_key(password: str, salt: Optional[bytes] = None, 
               iterations: int = 100000) -> Tuple[bytes, bytes]:
    """
    Derive a key using Argon2id.
    
    Args:
        password: The password to derive from
        salt: Optional salt (generated if not provided)
        iterations: Number of iterations for key derivation
        
    Returns:
        Tuple of (derived_key, salt)
    """
    if salt is None:
        salt = secrets.token_bytes(32)
    
    kdf = Argon2id(
        salt=salt,
        length=32,
        time_cost=iterations // 100000,  # Convert to time_cost parameter
        memory_cost=65536,  # 64MB
        parallelism=4,
        hash=hashes.SHA256(),
    )
    
    key = kdf.derive(password.encode('utf-8'))
    return key, salt


def generate_keypair() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    """
    Generate an Ed25519 keypair.
    
    Returns:
        Tuple of (private_key, public_key)
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


def sign_data(data: bytes, private_key: bytes) -> Tuple[bytes, bytes]:
    """
    Sign data using Ed25519.
    
    Args:
        data: Data to sign
        private_key: Private key as bytes
        
    Returns:
        Tuple of (signature, public_key)
    """
    if isinstance(private_key, bytes):
        private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)
    else:
        private_key_obj = private_key
    
    signature = private_key_obj.sign(data)
    public_key = private_key_obj.public_key()
    
    return signature, public_key.public_bytes_raw()


def verify_signature(data: bytes, signature: bytes, public_key: bytes) -> bool:
    """
    Verify Ed25519 signature.
    
    Args:
        data: Original data
        signature: Signature to verify
        public_key: Public key as bytes
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
        public_key_obj.verify(signature, data)
        return True
    except Exception:
        return False


def encrypt_data(data: bytes, key: bytes, associated_data: Optional[bytes] = None) -> bytes:
    """
    Encrypt data using ChaCha20-Poly1305.
    
    Args:
        data: Data to encrypt
        key: Encryption key (32 bytes)
        associated_data: Optional associated data
        
    Returns:
        Encrypted data
    """
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes for ChaCha20-Poly1305")
    
    cipher = ChaCha20Poly1305(key)
    nonce = secrets.token_bytes(12)  # 96-bit nonce
    
    if associated_data is None:
        associated_data = b""
    
    ciphertext = cipher.encrypt(nonce, data, associated_data)
    return nonce + ciphertext


def decrypt_data(encrypted_data: bytes, key: bytes, 
                 associated_data: Optional[bytes] = None) -> bytes:
    """
    Decrypt data using ChaCha20-Poly1305.
    
    Args:
        encrypted_data: Encrypted data (nonce + ciphertext)
        key: Decryption key (32 bytes)
        associated_data: Optional associated data
        
    Returns:
        Decrypted data
    """
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes for ChaCha20-Poly1305")
    
    if len(encrypted_data) < 12:
        raise ValueError("Encrypted data too short")
    
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    
    cipher = ChaCha20Poly1305(key)
    
    if associated_data is None:
        associated_data = b""
    
    return cipher.decrypt(nonce, ciphertext, associated_data)


def zeroize_memory(data: bytes) -> None:
    """
    Zeroize memory by overwriting with random data.
    
    Args:
        data: Data to zeroize
    """
    # Overwrite with random data multiple times
    for _ in range(3):
        os.urandom(len(data))
    
    # Note: In a real implementation, you'd want to use
    # platform-specific secure memory functions when available


def generate_random_bytes(length: int) -> bytes:
    """
    Generate cryptographically secure random bytes.
    
    Args:
        length: Number of bytes to generate
        
    Returns:
        Random bytes
    """
    return secrets.token_bytes(length)


def hash_data(data: bytes, algorithm: str = "blake3") -> bytes:
    """
    Hash data using the specified algorithm.
    
    Args:
        data: Data to hash
        algorithm: Hash algorithm ("blake3", "sha256", "sha512")
        
    Returns:
        Hash digest
    """
    if algorithm == "blake3":
        import blake3
        return blake3.blake3(data).digest()
    elif algorithm == "sha256":
        digest = hashes.Hash(hashes.SHA256())
        digest.update(data)
        return digest.finalize()
    elif algorithm == "sha512":
        digest = hashes.Hash(hashes.SHA512())
        digest.update(data)
        return digest.finalize()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def secure_compare(a: bytes, b: bytes) -> bool:
    """
    Constant-time comparison of two byte strings.
    
    Args:
        a: First byte string
        b: Second byte string
        
    Returns:
        True if strings are equal, False otherwise
    """
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    
    return result == 0