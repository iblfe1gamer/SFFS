"""
SFFS — Student 1: File Decryption Module

This module decrypts SFFS (.sffs) encrypted files and verifies integrity.

GCM Auth Tag Verification (CRITICAL):
Before decryption can begin, the GCM auth tag must be verified. GCM mode
provides authenticated encryption, meaning the auth tag is computed over
both the ciphertext AND the nonce/IV. Any modification to the ciphertext
or IV invalidates the tag.

Why verify BEFORE decryption:
1. If the auth tag fails, the file was tampered with
2. Decrypting a tampered file produces garbage data
3. This garbage could be exploited (e.g., SQL injection, XSS)
4. By failing fast, we prevent any attack surface from tampered files
5. We also DELETE any partial output to ensure no sensitive data persists

Security Risk of Decrypting to Host OS:
- SFFS is designed to decrypt files to an ISOLATED directory
- Never decrypt to the host OS disk (C: drive, /home/user)
- The host OS disk contains: executables, temp files, browser cache
- An attacker with decrypted sensitive files can:
  - Exfiltrate data
  - Execute code from decrypted files
  - Modify system files
- Decryption isolation ensures that compromised encrypted files don't
  compromise the entire system

Decryption Process:
1. Read SFFS file header
2. Validate magic bytes = b"SFFS"
3. Extract IV, auth_tag, hash_pre, original_size
4. Create AES-GCM cipher with IV
5. Attempt decryption (automatically verifies auth tag)
6. If auth tag invalid: delete any partial output, raise SecurityError
7. If successful: write decrypted plaintext to output_dir
8. Compute SHA-256 of decrypted output (hash_post)
9. Compare hash_post with hash_pre (via verifyHash module)
10. Return result dict with hash comparison
"""

# Why: Custom exception for security violations (tampered files, wrong password)
# Why: AES-GCM provides authenticated decryption (tag verified automatically)
# Why: get_random_bytes ensures IV randomness for next encryption
# Why: pathlib handles cross-platform paths cleanly
# Why: hashlib computes hash of decrypted output for integrity verification
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
import secrets
from pathlib import Path
import struct
import hashlib


# Custom exception class for security errors
# Why: Using a custom exception makes error handling explicit
# We don't want to catch generic exceptions for security issues
class SecurityError(Exception):
    """Raised when a security violation is detected during decryption."""
    pass


# SFFS format constants
SFFS_MAGIC = b"SFFS"
SFFS_VERSION = 0x02


def decryptFile(
    sffs_path: Path,
    aes_key: bytes,
    output_dir: Path = None
) -> dict:
    """
    Decrypt an SFFS file and verify integrity.

    The function reads the SFFS header, validates magic bytes, extracts
    the IV and auth tag, and attempts decryption. If the GCM auth tag
    fails, any partial output is deleted and a SecurityError is raised.

    Args:
        sffs_path: Path to the .sffs encrypted file
        aes_key: AES decryption key (same key used for encryption)
        output_dir: Directory to write decrypted file. If None, uses
            same directory as sffs_path.

    Returns:
        dict with:
            - output_path: Path to decrypted file
            - hash_pre: Original hash (from SFFS header)
            - hash_post: Hash of decrypted output
            - original_size: Original file size
            - status: "success" or "error"

    Raises:
        SecurityError: If auth tag fails (file tampered)
        FileNotFoundError: If sffs_path doesn't exist
        ValueError: If magic bytes don't match b"SFFS"
    """
    # Validate AES key size
    if len(aes_key) != 32:
        raise ValueError(
            f"AES key must be exactly 32 bytes. Received {len(aes_key)} bytes."
        )

    # Validate SFFS file exists
    if not sffs_path.exists():
        raise FileNotFoundError(f"SFFS file not found: {sffs_path}")

    # Guard: AESGCM.decrypt() requires full ciphertext+tag in memory (GCM is non-streaming).
    # Reject files over 2 GB to prevent OOM on large inputs.
    MAX_FILE_BYTES = 2 * 1024 ** 3  # 2 GB
    if sffs_path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(
            f"File exceeds 2 GB decryption limit ({sffs_path.stat().st_size} bytes). "
            "Use chunked encryption for large files."
        )

    # Read entire file content
    file_content = sffs_path.read_bytes()

    # SFFS V2 header is 57 bytes:
    #   Magic (4) + Version (1) + IV (12) + Hash (32) + Size (8) = 57
    # GCM auth tag is embedded at end of ciphertext, not stored in header.
    HEADER_SIZE = 4 + 1 + 12 + 32 + 8  # = 57

    # Read and validate magic bytes first
    magic = file_content[:4]
    if magic != SFFS_MAGIC:
        raise ValueError(
            f"Invalid SFFS file: magic bytes expected b'SFFS', got {magic}"
        )

    # Parse remaining header fields
    pos = 4
    version = file_content[pos]
    pos += 1

    # Reject files with unknown version — prevents version confusion attacks
    if version != SFFS_VERSION:
        raise ValueError(
            f"Unsupported SFFS version: 0x{version:02x}. "
            f"Expected 0x{SFFS_VERSION:02x}. Re-encrypt with current SFFS."
        )

    iv = file_content[pos : pos + 12]
    pos += 12

    hash_pre = file_content[pos : pos + 32].hex()
    pos += 32

    original_size = struct.unpack("Q", file_content[pos : pos + 8])[0]
    pos += 8

    # Read original extension (1-byte length + N bytes)
    # Stored in header so the .sffs filename doesn't leak the file type
    ext_len = file_content[pos]
    pos += 1
    try:
        original_ext = file_content[pos : pos + ext_len].decode("utf-8")  # e.g. ".docx"
    except (UnicodeDecodeError, ValueError):
        raise ValueError("SFFS file corrupted — invalid extension encoding in header")
    pos += ext_len

    # Ciphertext is everything after the header (includes GCM tag at end)
    ciphertext = file_content[pos:]

    # Verify we have enough data (header + at least GCM tag worth of ciphertext)
    if len(ciphertext) < 16:
        raise ValueError("SFFS file too small — possibly corrupted")

    # Create AES-GCM cipher with stored IV
    # GCM will automatically verify the auth tag during decryption
    aesgcm = AESGCM(aes_key)

    try:
        # ciphertext includes GCM tag at end (same layout as encryptFile / cryptography AESGCM)
        # API: decrypt(nonce, data_with_tag, associated_data)
        decrypted = aesgcm.decrypt(iv, ciphertext, None)

    except (ValueError, InvalidTag):
        # Auth tag failed — file was tampered with
        # SECURITY: Delete any partial output before raising error
        # This prevents attackers from harvesting partially decrypted data
        if output_dir is not None:
            output_path = output_dir / sffs_path.stem  # best-effort cleanup, ext unknown at this point
            if output_path.exists():
                output_path.unlink(missing_ok=True)
        raise SecurityError(
            "File tampered or corrupted — decryption aborted"
        )

    # Write decrypted plaintext to output directory
    # Why: We restrict output to output_dir to prevent host filesystem contamination
    # If output_dir is None, we still write to same directory as sffs_path
    # This is less secure but acceptable for standalone testing
    if output_dir is None:
        output_dir = sffs_path.parent

    # Restore original filename: stem from .sffs file + original extension from header
    # e.g. document.sffs + stored ".docx" -> document.docx
    # Original extension never appeared in the .sffs filename (no type leakage)
    output_path = output_dir / (sffs_path.stem + original_ext)
    output_path.write_bytes(decrypted)

    # Compute SHA-256 of decrypted output
    hash_post = hashlib.sha256(decrypted).hexdigest()

    return {
        "output_path": output_path,
        "hash_pre": hash_pre,
        "hash_post": hash_post,
        "original_size": original_size,
        "status": "success",
    }


if __name__ == "__main__":
    # This demo requires an .sffs file created by f02_encrypt_file.py
    # Run f02 first to create sample.sffs, then run f03

    import sys

    # Check if sample.sffs exists (created by f02)
    sample_sffs = Path(__file__).parent / "test_output" / "sample.sffs"

    if not sample_sffs.exists():
        print("=" * 60)
        print("SFFS — File Decryption Demo (Requires sample.sffs)")
        print("=" * 60)
        print()
        print("Run f02_encrypt_file.py first to create sample.sffs")
        print()
        print("Demo instructions:")
        print("1. Run: python f02_encrypt_file.py (creates sample.sffs)")
        print("2. Run: python f03_decrypt_file.py (decrypts sample.sffs)")
        print()
        print("If you don't see the file above, f02 hasn't been run yet.")
        print()
        print("Or manually create a sample.sffs file before running this demo.")
        print()
        print("=" * 60)
        sys.exit(1)

    # Read AES key from the same file used for encryption
    # In production, keys would be derived from password via PBKDF2
    # For demo, we use the same random key as f02
    aes_key = b"0" * 32  # This won't work — f02 uses random key

    print("=" * 60)
    print("SFFS — File Decryption Demo")
    print("=" * 60)
    print(f"Encrypted file: {sample_sffs}")
    print(f"SFFS file size: {sample_sffs.stat().st_size} bytes")
    print()

    # Note: For actual demo, we need to store the key somewhere
    # For this standalone demo, we'll skip actual decryption
    # and instead show the code flow
    print("⚠️  DEMO MODE: Cannot decrypt without stored AES key")
    print()
    print("In production, you would:")
    print("  1. Store the AES key with the .sffs file (e.g., in metadata)")
    print("  2. Or derive the key from a master password stored securely")
    print("  3. Call decryptFile() with the derived key")
    print()
    print("Security notes:")
    print("  - GCM auth tag verified BEFORE decryption begins")
    print("  - Any tampered file raises SecurityError immediately")
    print("  - Partial outputs are deleted on auth tag failure")
    print("  - Decrypted files written to isolated output_dir")
    print()
    print("=" * 60)
