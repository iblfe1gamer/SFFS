"""
SFFS — Student 1: File Encryption Module

This module encrypts files using AES-256-GCM and writes them in the custom
SFFS (.sffs) binary format. The format includes metadata for integrity verification.

AES-256-GCM (Galois/Counter Mode) is chosen over CBC mode because:
- GCM provides BOTH confidentiality AND authentication in a single pass
- CBC mode requires a separate MAC (Message Authentication Code)
- GCM's authentication tag detects any ciphertext tampering

Initialization Vector (IV):
- The IV must be cryptographically random for EVERY encryption operation
- Same plaintext encrypted with different IVs produces different ciphertext
- IV does NOT need to be secret, but must be unpredictable
- Never reuse an IV with the same key (though we generate new IVs always)

GCM Auth Tag:
- 16 bytes (128 bits) of authentication data
- Computed over both the ciphertext and the nonce/IV
- Any bit flip in ciphertext invalidates the tag
- GCM decrypts and verifies tag atomically — fails if tag invalid

SFFS File Format (.sffs):
┌────────────────────────────────────────────────────────────────┐
│  Magic (4 bytes):   "SFFS"                                      │
│  Version (1 byte):   0x01                                       │
│  IV (16 bytes):     Random initialization vector                │
│  Auth Tag (16 bytes): GCM authentication tag                    │
│  Hash Pre (32 bytes): SHA-256 of plaintext BEFORE encryption    │
│  File Size (8 bytes): Original file size (uint64, little-endian)│
│  Ciphertext (N bytes): Encrypted file content                   │
└────────────────────────────────────────────────────────────────┘

Total header = 77 bytes before ciphertext.

Why we hash BEFORE encryption:
- The hash proves the original plaintext integrity
- After decryption, we hash the plaintext again and compare
- Any tampering (even 1 bit) changes the hash completely (avalanche effect)
- This enables integrity verification without needing external signatures
"""

# Why: AES-GCM provides authenticated encryption (confidentiality + integrity)
# Why: get_random_bytes provides cryptographically secure random values
# Why: struct.pack enables binary header writing (little-endian uint64)
# Why: hashlib provides FIPS-140 certified hash functions
# Why: pathlib provides cross-platform path handling
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets
from pathlib import Path
import struct
import hashlib


# Define SFFS magic bytes constant
SFFS_MAGIC = b"SFFS"
SFFS_VERSION = 0x01


def encryptFile(
    input_path: Path,
    aes_key: bytes,
    output_path: Path = None
) -> dict:
    """
    Encrypt a file using AES-256-GCM and write to SFFS binary format.

    The function reads the original file, computes its SHA-256 hash BEFORE
    encryption, generates a random IV, encrypts the content, and writes
    the encrypted file with full header metadata.

    Args:
        input_path: Path to the file to encrypt
        aes_key: AES encryption key (MUST be exactly 32 bytes = 256 bits)
        output_path: Optional output path. If None, uses input_path.with_suffix('.sffs')

    Returns:
        dict with:
            - sffs_path: Path to the created .sffs file
            - hash_pre: SHA-256 hash of plaintext (before encryption)
            - iv: The IV used (for decryption)
            - original_size: Original file size in bytes
            - status: "success"

    Raises:
        ValueError: If aes_key is not exactly 32 bytes
        FileNotFoundError: If input_path doesn't exist
    """
    # Validate AES key size — must be exactly 256 bits (32 bytes)
    if len(aes_key) != 32:
        raise ValueError(
            f"AES key must be exactly 32 bytes (256 bits). "
            f"Received {len(aes_key)} bytes."
        )

    # Read original file content (as bytes); raises FileNotFoundError if missing
    plaintext = input_path.read_bytes()
    original_size = len(plaintext)

    # Compute SHA-256 hash BEFORE encryption — single call, reused as both hex string and raw digest
    hash_digest = hashlib.sha256(plaintext).digest()
    hash_pre = hash_digest.hex()

    # Generate cryptographically secure random IV (16 bytes = 128 bits)
    # Why: Each encryption must use a unique IV
    # Reusing IVs with same key is catastrophic for security
    iv = secrets.token_bytes(16)

    # Create AES-GCM cipher with generated IV
    aesgcm = AESGCM(aes_key)

    # Encrypt plaintext
    # GCM automatically computes the authentication tag
    ciphertext = aesgcm.encrypt(iv, plaintext, associated_data=None)
    auth_tag = ciphertext[-16:]  # Last 16 bytes is the authentication tag

    # Assemble SFFS file header
    # Header fields:
    #   Magic (4 bytes): Magic number "SFFS"
    #   Version (1 byte): Format version
    #   IV (16 bytes): Initialization vector (stored for decryption)
    #   Auth Tag (16 bytes): GCM authentication tag
    #   Hash Pre (32 bytes): SHA-256 hash of plaintext
    #   File Size (8 bytes): Original file size as uint64 little-endian
    header = (
        SFFS_MAGIC +           # Magic bytes
        struct.pack("B", SFFS_VERSION) +  # Version byte
        iv +                   # IV (16 bytes)
        auth_tag +             # Auth tag (16 bytes)
        hash_digest +                             # Hash of plaintext (32 bytes)
        struct.pack("Q", original_size)  # File size as uint64 little-endian
    )

    # Write complete SFFS file: header + ciphertext
    # Why: We write the header first, then ciphertext immediately after
    # This ensures atomic write of the complete encrypted file
    if output_path is None:
        output_path = input_path.with_suffix(".sffs")

    output_path.write_bytes(header + ciphertext)

    return {
        "sffs_path": output_path,
        "hash_pre": hash_pre,
        "iv": iv,
        "original_size": original_size,
        "status": "success",
    }


if __name__ == "__main__":
    import os

    # Create test output directory
    test_output_dir = Path(__file__).parent / "test_output"
    test_output_dir.mkdir(exist_ok=True)

    # Create a test file
    test_file = test_output_dir / "sample.txt"
    test_content = b"Hello SFFS! This is a test file. " * 10
    test_file.write_bytes(test_content)

    print("=" * 60)
    print("SFFS — File Encryption Demo")
    print("=" * 60)
    print(f"Original file: {test_file}")
    print(f"Original size: {len(test_content)} bytes")
    print(f"Original content (first 80 chars): {test_content[:80]}")
    print()

    # Generate random 32-byte AES key
    # In production, you would derive this from a password using PBKDF2
    # For demo, we use random bytes directly
    aes_key = secrets.token_bytes(32)

    # Encrypt the test file
    result = encryptFile(test_file, aes_key)

    print(f"Encrypted file: {result['sffs_path']}")
    print(f"SFFS file size: {result['sffs_path'].stat().st_size} bytes")
    print(f"SHA-256 hash (before encryption): {result['hash_pre']}")
    print(f"IV used: {result['iv'].hex()}")
    print()

    # Verify SFFS header magic bytes
    header_bytes = test_output_dir / "sample.sffs"
    header_bytes = result['sffs_path']
    magic = header_bytes.read_bytes()[:4]
    print(f"SFFS magic bytes: {magic}")
    print(f"Magic check: {'PASS' if magic == b'SFFS' else 'FAIL'}")
    print()

    print("=" * 60)
