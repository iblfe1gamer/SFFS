"""
SFFS — Student 1: RSA Key Pair Generation Module

This module generates RSA-2048 key pairs for use in the Smart File Fortify System (SFFS).

RSA (Rivest-Shamir-Adleman) is the most widely used public-key cryptosystem. It enables
secure communication between parties who have never met before by using asymmetric
encryption: a public key for encrypting data, and a private key for decrypting it.

Why 2048-bit is the industry standard:
- 2048-bit RSA provides ~112 bits of security (equivalent to 112-bit symmetric key)
- Current best attacks can only break 1024-bit RSA, making 2048-bit secure for now
- NIST recommends at least 2048-bit for new deployments
- 4096-bit is overkill for most applications and slower

CRITICAL SECURITY NOTE:
- The PRIVATE KEY must NEVER be stored in plain text on disk
- This function generates the private key in memory and returns it as bytes
- The caller must immediately pass private_key_bytes to secureKeyStorage()
- Storing private keys as plain text files is a security vulnerability
- Even encrypted private keys should be stored in secure vaults, not local disks

Key Lifecycle in SFFS:
1. generateKeyPairs() - generates keys, returns private key as bytes only
2. secureKeyStorage() - immediately wraps and stores private key with PBKDF2 + AES
3. retrieveKey() - decrypts and returns private key only after password verification
4. encryptFile() - uses AES key derived from master password via the stored private key
"""

# Why: cryptography.hazmat provides well-maintained crypto primitives
# Why: serialization handles PEM encoding for key storage
# Why: pathlib.Path provides cross-platform path handling
# Why: secrets generates cryptographically secure random values
# Why: datetime provides ISO timestamp for auditability
from cryptography.hazmat.primitives.serialization import (
    PrivateFormat,
    NoEncryption,
    PublicFormat,
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from pathlib import Path
import secrets
import hashlib
import datetime


def generateKeyPairs(output_dir: Path, key_size: int = 2048) -> dict:
    """
    Generate an RSA-2048 key pair for SFFS encryption/decryption.

    RSA asymmetric encryption uses a mathematical relationship between two keys:
    - Public key: safely shareable, used to encrypt data or verify signatures
    - Private key: must be kept secret, used to decrypt data or create signatures

    Args:
        output_dir: Directory where the public key will be saved
        key_size: RSA key size in bits (default 2048, minimum 2048)

    Returns:
        dict with keys:
            - public_key_path: Path to saved public key (.pem file)
            - private_key_bytes: RSA private key as bytes (DO NOT write to disk!)
            - key_id: First 8 chars of SHA-256 hash of public key (unique identifier)
            - generated_at: ISO timestamp of key generation

    Raises:
        ValueError: If key_size < 2048 (insufficient security)

    Security Notes:
        - private_key_bytes must be passed immediately to secureKeyStorage()
        - Never log, print, or store private_key_bytes in any persistent storage
        - The private key exists only in memory after this function returns
    """
    # Validate key size — 2048-bit is minimum for acceptable security
    if key_size < 2048:
        raise ValueError(
            f"RSA key size must be at least 2048 bits for security. "
            f"Requested {key_size} bits (minimum 2048)."
        )

    # Generate RSA key pair using cryptography library
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend(),
    )

    # Export public key to PEM format (safe to share, human-readable)
    # Why: PEM format is standard, widely supported, and base64-encoded
    public_key = key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Write public key to file — this is safe because it cannot decrypt data
    # Only the private key can decrypt, and we never write that to disk here
    public_key_path = output_dir / "public_key.pem"
    public_key_path.write_bytes(public_pem)

    # Export private key as bytes only — DO NOT write to disk directly
    # We use NoEncryption because we immediately encrypt with PBKDF2 + AES
    # in secureKeyStorage(). Writing unencrypted private key to disk is a
    # critical security vulnerability.
    private_key_bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption(),
    )

    # Generate key_id from public key hash
    # Why: key_id provides a unique, deterministic identifier for the key pair
    # This allows us to reference keys without exposing them
    key_id = hashlib.sha256(public_pem).hexdigest()[:8]

    # Generate ISO timestamp for audit trail
    generated_at = datetime.datetime.now().isoformat()

    # Return key information — private key bytes must be used immediately
    return {
        "public_key_path": public_key_path,
        "private_key_bytes": private_key_bytes,
        "key_id": key_id,
        "generated_at": generated_at,
    }


if __name__ == "__main__":
    # Create output directory for test keys
    test_output_dir = Path(__file__).parent / "test_output"
    test_output_dir.mkdir(exist_ok=True)

    # Generate RSA key pair
    result = generateKeyPairs(test_output_dir, key_size=2048)

    # Display results
    print("=" * 60)
    print("SFFS — RSA Key Pair Generation Demo")
    print("=" * 60)
    print(f"Key ID: {result['key_id']}")
    print(f"Generated at: {result['generated_at']}")
    print(f"Public key saved to: {result['public_key_path']}")
    print(f"Private key (bytes): {len(result['private_key_bytes'])} bytes")
    print()
    print("SECURITY NOTICE:")
    print("    Private key bytes NOT written to disk — pass to secureKeyStorage()")
    print()
    print("Public key PEM (first 5 lines):")
    lines = result["public_key_path"].read_text().split("\n")
    for line in lines[:5]:
        print(f"    {line}")
    print()
    print("=" * 60)
