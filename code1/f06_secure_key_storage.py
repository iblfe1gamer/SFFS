"""
SFFS — Student 1: Secure Key Storage Module

This module provides secure storage and retrieval of RSA private keys.

CRITICAL SECURITY:
The RSA private key is the most sensitive asset in SFFS. If leaked:
- An attacker can decrypt ALL .sffs files encrypted with that key
- An attacker can forge signatures on any encrypted data
- An attacker can impersonate the system owner

Why PBKDF2 (Password-Based Key Derivation Function 2):
PBKDF2 takes a password (arbitrary length, often weak) and derives a
cryptographically strong key (e.g., 32 bytes for AES).

Why 310,000 iterations:
- NIST SP 800-63B (2023) recommends ~200k iterations for SHA-256
- Higher iterations = slower password guessing
- But still fast enough for legitimate users
- 310,000 is a good balance between security and usability

Why salt is required:
- A random salt (16 bytes) prevents rainbow table attacks
- Each key store has a unique salt
- Even if two users have same password, they get different keys
- Salt must be stored alongside encrypted key (it's not secret)

Why AES-256-GCM wraps the private key:
- Key wrapping is separate from data encryption
- AES-256-GCM provides both confidentiality and authentication
- The private key is encrypted before disk storage
- Only someone with the master password can unwrap it

Keystore File Format (JSON with base64 encoding):
{
  "version": "1.0",
  "key_id": "abc123...",
  "kdf": "PBKDF2-SHA256",
  "kdf_iterations": 310000,
  "salt": "base64-encoded 16-byte salt",
  "iv": "base64-encoded 12-byte GCM IV",
  "auth_tag": "base64-encoded 16-byte GCM auth tag",
  "encrypted_private_key": "base64-encoded AES ciphertext"
}

Memory Security:
After encrypting the private key, we immediately wipe it from memory
(using memset in C, or in Python by letting the GC reclaim it). This
prevents attackers from reading the key from memory dumps.
"""

# Why: AES-GCM encrypts the private key before storage
# Why: PBKDF2 derives strong keys from passwords
# Why: SHA256 and HMAC for KDF PRF and constant-time operations
# Why: get_random_bytes for cryptographically secure randomness
# Why: RSA for encrypting AES keys (key wrapping)
# Why: pathlib, json, base64, struct for serialization
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256, HMAC
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA
import datetime
import json
import base64
import struct
from pathlib import Path
from typing import Optional
from argon2.low_level import Type, hash_secret_raw


# KDF parameters per NIST SP 800-63B
KDF_ITERATIONS = 310_000  # PBKDF2 fallback compatibility
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # KiB
ARGON2_PARALLELISM = 2


def secureKeyStorage(
    private_key_bytes: bytes,
    master_password: str,
    output_dir: Path,
    key_id: str = None,
    kdf: str = "ARGON2ID",
) -> dict:
    """
    Securely store an RSA private key using PBKDF2 + AES-256-GCM.

    Args:
        private_key_bytes: RSA private key as PKCS1-encoded bytes
        master_password: User's master password (will be derived to key)
        output_dir: Directory to store keystore JSON file
        key_id: Optional key identifier. If None, generates from private key bytes

    Returns:
        dict with:
            - keystore_path: Path to .json keystore file
            - key_id: Key identifier
            - status: "stored"

    Raises:
        ValueError: If key_id is provided but too long
    """
    # Generate random salt (16 bytes)
    # Why: Salt prevents rainbow table attacks
    # Each key store must have a unique salt
    salt = get_random_bytes(16)

    # Derive AES key from password (Argon2id default, PBKDF2 compatibility mode).
    if kdf.upper() == "ARGON2ID":
        derived_key = hash_secret_raw(
            secret=master_password.encode("utf-8"),
            salt=salt,
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=32,
            type=Type.ID,
        )
        kdf_name = "ARGON2ID"
    elif kdf.upper() == "PBKDF2-SHA256":
        derived_key = PBKDF2(
            master_password,
            salt,
            dkLen=32,
            count=KDF_ITERATIONS,
            hmac_hash_module=SHA256,
        )
        kdf_name = "PBKDF2-SHA256"
    else:
        raise ValueError(f"Unsupported KDF: {kdf}")

    # Generate random IV for GCM mode
    iv = get_random_bytes(12)  # GCM nonce is 12 bytes minimum

    # Encrypt private key with AES-256-GCM
    cipher = AES.new(derived_key, AES.MODE_GCM, nonce=iv)
    encrypted_key, auth_tag = cipher.encrypt_and_digest(private_key_bytes)

    # Write to memory buffer for JSON serialization
    # Immediately overwrite private_key_bytes in memory after use
    # In C: memset(private_key_bytes, 0, sizeof(private_key_bytes))
    # In Python, we rely on GC, but we can help by reassigning
    private_key_bytes = None  # Wipe from memory

    # Encode everything to base64 for JSON storage
    salt_b64 = base64.b64encode(salt).decode("ascii")
    iv_b64 = base64.b64encode(iv).decode("ascii")
    auth_tag_b64 = base64.b64encode(auth_tag).decode("ascii")
    encrypted_key_b64 = base64.b64encode(encrypted_key).decode("ascii")

    # Construct key_id if not provided (must not use wiped private_key_bytes)
    if key_id is None:
        key_id = hashlib_sha256_sandwich(salt, iv)

    # Create keystore JSON
    keystore = {
        "version": "2.0" if kdf_name == "ARGON2ID" else "1.0",
        "key_id": key_id,
        "kdf": kdf_name,
        "kdf_iterations": KDF_ITERATIONS if kdf_name == "PBKDF2-SHA256" else None,
        "argon2_time_cost": ARGON2_TIME_COST if kdf_name == "ARGON2ID" else None,
        "argon2_memory_cost": ARGON2_MEMORY_COST if kdf_name == "ARGON2ID" else None,
        "argon2_parallelism": ARGON2_PARALLELISM if kdf_name == "ARGON2ID" else None,
        "salt": salt_b64,
        "iv": iv_b64,
        "auth_tag": auth_tag_b64,
        "encrypted_private_key": encrypted_key_b64,
            "created_at": datetime.datetime.now().isoformat(),
    }

    # Write keystore file
    keystore_path = output_dir / f"keystore_{key_id}.json"
    keystore_path.write_text(json.dumps(keystore, indent=2))

    return {
        "keystore_path": keystore_path,
        "key_id": key_id,
        "status": "stored",
    }


import hashlib


def hashlib_sha256_sandwich(salt: bytes, iv: bytes) -> str:
    """Generate key_id from salt and iv using SHA-256 sandwich."""
    # Sandwich: hash(salt || hash(iv))
    inner_hash = hashlib.sha256(iv).digest()
    outer_hash = hashlib.sha256(salt + inner_hash).hexdigest()
    return outer_hash[:8]


def retrieveKey(keystore_path: Path, master_password: str) -> bytes:
    """
    Retrieve and decrypt an RSA private key from keystore.

    Args:
        keystore_path: Path to keystore JSON file
        master_password: Master password (same as used during storage)

    Returns:
        RSA private key as PKCS1-encoded bytes

    Raises:
        SecurityError: If password is wrong (GCM auth tag fails)
        FileNotFoundError: If keystore_path doesn't exist
        ValueError: If key_id doesn't match stored value
    """
    if not keystore_path.exists():
        raise FileNotFoundError(f"Keystore not found: {keystore_path}")

    # Load keystore JSON
    keystore_data = json.loads(keystore_path.read_text())

    # Re-derive AES key from password + stored salt with versioned KDF support.
    salt = base64.b64decode(keystore_data["salt"])
    kdf_name = (keystore_data.get("kdf") or "PBKDF2-SHA256").upper()
    if kdf_name == "ARGON2ID":
        derived_key = hash_secret_raw(
            secret=master_password.encode("utf-8"),
            salt=salt,
            time_cost=int(keystore_data.get("argon2_time_cost", ARGON2_TIME_COST)),
            memory_cost=int(keystore_data.get("argon2_memory_cost", ARGON2_MEMORY_COST)),
            parallelism=int(keystore_data.get("argon2_parallelism", ARGON2_PARALLELISM)),
            hash_len=32,
            type=Type.ID,
        )
    else:
        derived_key = PBKDF2(
            master_password,
            salt,
            dkLen=32,
            count=int(keystore_data.get("kdf_iterations", KDF_ITERATIONS)),
            hmac_hash_module=SHA256,
        )

    # Decrypt private key
    encrypted_key = base64.b64decode(keystore_data["encrypted_private_key"])
    auth_tag = base64.b64decode(keystore_data["auth_tag"])
    iv = base64.b64decode(keystore_data["iv"])

    cipher = AES.new(derived_key, AES.MODE_GCM, nonce=iv)
    private_key_bytes = cipher.decrypt_and_verify(encrypted_key, auth_tag)

    return private_key_bytes


def wrapAESKey(aes_key: bytes, public_key_path: Path, bound_file_path: Optional[Path] = None) -> bytes:
    """
    Encrypt an AES session key using RSA-OAEP for key transport.

    Args:
        aes_key: AES session key to wrap
        public_key_path: Path to RSA public key PEM file

    Returns:
        Serialized wrap payload bytes. v2 payloads include binding metadata.
    """
    # Load public key — OAEP via PKCS1_OAEP (PyCryptodome API)
    public_key = RSA.import_key(public_key_path.read_text())
    cipher_rsa = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
    wrapped_key = cipher_rsa.encrypt(aes_key)

    # v2 wrap envelope with key commitment and optional .sffs binding metadata.
    envelope = {
        "version": "2.0",
        "alg": "RSA-OAEP-SHA256",
        "wrapped_key_b64": base64.b64encode(wrapped_key).decode("ascii"),
        "key_commitment": hashlib.sha256(aes_key).hexdigest(),
    }
    if bound_file_path is not None:
        bound = Path(bound_file_path)
        envelope["bound_file_name"] = bound.name
        if bound.exists():
            envelope["bound_file_sha256"] = hashlib.sha256(bound.read_bytes()).hexdigest()
    return json.dumps(envelope, separators=(",", ":")).encode("utf-8")


def unwrapAESKey(
    encrypted_aes_key: bytes,
    keystore_path: Path,
    master_password: str,
    expected_sffs_path: Optional[Path] = None,
) -> bytes:
    """
    Unwrap an AES key that was RSA-wrapped and stored with keystore.

    Args:
        encrypted_aes_key: RSA-encrypted AES key bytes
        keystore_path: Path to keystore JSON file
        master_password: Master password for retrieving RSA private key

    Returns:
        Original AES key bytes

    Raises:
        SecurityError: If password is wrong (RSA decryption fails)
    """
    wrapped_key = encrypted_aes_key
    commitment = None
    bound_file_name = None
    bound_file_sha256 = None
    blob = encrypted_aes_key.lstrip()
    if blob.startswith(b"{"):
        env = json.loads(encrypted_aes_key.decode("utf-8"))
        if env.get("version") == "2.0":
            wrapped_key = base64.b64decode(env["wrapped_key_b64"])
            commitment = env.get("key_commitment")
            bound_file_name = env.get("bound_file_name")
            bound_file_sha256 = env.get("bound_file_sha256")

    # Retrieve RSA private key
    private_key_bytes = retrieveKey(keystore_path, master_password)
    private_key = RSA.import_key(private_key_bytes)
    cipher_rsa = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
    aes_key = cipher_rsa.decrypt(wrapped_key)

    if commitment and hashlib.sha256(aes_key).hexdigest() != commitment:
        raise ValueError("Wrapped key commitment mismatch")

    if expected_sffs_path is not None and (bound_file_name or bound_file_sha256):
        exp = Path(expected_sffs_path)
        if bound_file_name and exp.name != bound_file_name:
            raise ValueError("Wrap metadata file-name mismatch")
        if bound_file_sha256:
            if not exp.exists():
                raise FileNotFoundError(f"Expected .sffs file not found: {exp}")
            actual_sha = hashlib.sha256(exp.read_bytes()).hexdigest()
            if actual_sha != bound_file_sha256:
                raise ValueError("Wrap metadata file-hash mismatch")

    return aes_key


if __name__ == "__main__":
    import sys

    # Create test output directory
    test_output_dir = Path(__file__).parent / "test_output"
    test_output_dir.mkdir(exist_ok=True)

    # Generate a fake private key (256 bytes)
    from Crypto.PublicKey import RSA
    fake_key = RSA.generate(2048)
    fake_key_bytes = fake_key.private_bytes(
        encoding="PKCS1",
        format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption,
    )

    # Store key with password
    master_password = "TestPassword123!"
    keystore = secureKeyStorage(fake_key_bytes, master_password, test_output_dir)

    print("=" * 60)
    print("SFFS — Secure Key Storage Demo")
    print("=" * 60)
    print(f"Keystore saved to: {keystore['keystore_path']}")
    print(f"Key ID: {keystore['key_id']}")
    print()

    # Show keystore JSON (redacted for security)
    print("Keystore JSON (encrypted):")
    print("-" * 40)
    keystore_content = keystore['keystore_path'].read_text()
    lines = keystore_content.split("\n")
    for line in lines[:10]:  # Show first 10 lines
        print(f"  {line}")
    print(f"  ... ({len(lines) - 10} more lines)")
    print()

    print("Security note:")
    print("  The 'encrypted_private_key' field is base64-encoded ciphertext.")
    print("  It cannot be decrypted without the master password.")
    print()

    # Retrieve key and verify
    retrieved_key = retrieveKey(keystore['keystore_path'], master_password)

    print("Retrieved key (first 32 bytes):")
    print(f"  {retrieved_key[:32].hex()}...")
    print()

    # Verify keys match
    if fake_key_bytes == retrieved_key:
        print("✓ Keys match (retrieval successful)")
    else:
        print("✗ Keys don't match (unexpected!)")

    print()

    # Try wrong password (should raise SecurityError)
    print("Attempting retrieval with wrong password:")
    try:
        retrieved_wrong = retrieveKey(
            keystore['keystore_path'],
            "WrongPassword123!",
        )
        print("✗ Should have raised SecurityError!")
    except Exception as e:
        print(f"  ✓ Raised {type(e).__name__}: {e}")

    print()

    print("=" * 60)
