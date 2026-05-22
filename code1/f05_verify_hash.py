"""
SFFS — Student 1: Hash Verification Module

This module verifies file integrity by comparing cryptographic hashes.

Timing Attacks (Why hmac.compare_digest is CRITICAL):
A timing attack measures how long a comparison takes to determine if
values match. In Python, `==` returns early on first mismatch:

    "abc" == "abcdabc"  # Fast — mismatch at position 3
    "abc" == "abxc"     # Slower — match first 3 chars, mismatch at 4

An attacker can send many requests, measure response times, and determine
if any prefix matches. This allows them to brute-force passwords, tokens,
or hashes one character at a time.

hmac.compare_digest() is a constant-time comparison function that takes
the SAME time regardless of where the mismatch occurs. This prevents
timing attacks.

What hash_pre and hash_post prove:
- hash_pre: SHA-256 of plaintext BEFORE encryption (stored in .sffs header)
- hash_post: SHA-256 of plaintext AFTER decryption (computed locally)
- If hash_pre == hash_post: File integrity verified, no tampering detected
- If hash_pre != hash_post: File was modified (tampered) or corrupted

Real-World Threat: Man-in-the-Middle (MitM)
1. Attacker intercepts .sffs file in transit
2. Attacker modifies ciphertext (e.g., flips bits)
3. Attacker forwards modified file to victim
4. Victim decrypts file successfully (if only ciphertext changed)
5. Decrypted plaintext is garbage (but could be malicious)
6. hash_post won't match hash_pre — attack detected!

Without hash verification, step 5 would be undetected.
"""

# Why: hmac.compare_digest prevents timing attacks (constant-time comparison)
# Why: hashlib provides FIPS-140 certified hash functions
# Why: pathlib handles file paths cleanly
# Why: hmac module provides secure comparison functions
import hmac
import struct
from hashlib import sha256
from pathlib import Path
from typing import Union
from f04_generate_hash import generateHash


def verifyHash(hash_pre: str, hash_post: str) -> dict:
    """
    Verify that two hashes match using constant-time comparison.

    Args:
        hash_pre: Expected hash (from .sffs header or trusted source)
        hash_post: Computed hash (from decrypted file)

    Returns:
        dict with:
            - match: True if hashes identical, False otherwise
            - alert_level: "OK" or "CRITICAL_TAMPER_DETECTED"
            - hash_pre: Expected hash (truncated for safety)
            - hash_post: Computed hash (truncated for safety)
            - message: Human-readable status message
    """
    # Use hmac.compare_digest for constant-time comparison
    # This prevents timing attacks where early mismatch detection
    # could leak information about the expected hash
    is_match = hmac.compare_digest(hash_pre, hash_post)

    # Determine alert level and message
    if is_match:
        alert_level = "OK"
        message = "File integrity verified — no tampering detected"
    else:
        alert_level = "CRITICAL_TAMPER_DETECTED"
        message = "WARNING: File hash mismatch — file may have been tampered with"

    # Return truncated hashes for security (prevent hash leakage)
    return {
        "match": is_match,
        "alert_level": alert_level,
        "hash_pre": hash_pre[:16] + "..." if len(hash_pre) > 16 else hash_pre,
        "hash_post": hash_post[:16] + "..." if len(hash_post) > 16 else hash_post,
        "message": message,
    }


def verifyFileIntegrity(original_path: Path, decrypted_path: Path) -> dict:
    """
    Verify integrity of a file by comparing hashes of original and decrypted versions.

    Args:
        original_path: Path to the original file (or the .sffs file's hash)
        decrypted_path: Path to the decrypted file

    Returns:
        dict with same keys as verifyHash(), plus:
            - original_path: Path used for original hash
            - decrypted_path: Path of decrypted file

    Note:
        If original_path is a .sffs file, this reads its header hash_pre.
        If original_path is a plain file, it hashes the file directly.
    """
    # Handle .sffs files (read hash from header)
    if str(original_path).endswith(".sffs"):
        with open(original_path, "rb") as f:
            # SFFS V2 header: magic(4) + version(1) + IV(12) = 17 bytes to skip
            f.read(4 + 1 + 12)
            # Read hash_pre (32 bytes)
            hash_pre_bytes = f.read(32)
            hash_pre = hash_pre_bytes.hex()
            # Skip orig_size(8) + ext_len(1) + ext(N) — not needed for hash verification
            f.read(8)
            ext_len = struct.unpack("B", f.read(1))[0]
            f.read(ext_len)

        # Compute hash of decrypted file using streaming (handles large files)
        hash_post = generateHash(decrypted_path, "sha256")

    # Handle plain file comparison — stream both files to avoid OOM on large inputs
    elif original_path.exists():
        hash_pre = generateHash(original_path, "sha256")
        hash_post = generateHash(decrypted_path, "sha256")

    else:
        raise FileNotFoundError(f"Original file not found: {original_path}")

    # Verify hashes
    result = verifyHash(hash_pre, hash_post)
    result["original_path"] = original_path
    result["decrypted_path"] = decrypted_path

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("SFFS — Hash Verification Demo")
    print("=" * 60)
    print()

    # Demo 1: Matching hashes (OK)
    print("Demo 1: Matching Hashes (Integrity Verified)")
    print("-" * 40)
    hash_pre = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    hash_post = hash_pre  # Same hash

    result = verifyHash(hash_pre, hash_post)
    print(f"Hash pre:  {result['hash_pre']}")
    print(f"Hash post: {result['hash_post']}")
    print(f"Match: {result['match']}")
    print(f"Alert: {result['alert_level']}")
    print(f"Message: {result['message']}")
    print()

    # Demo 2: Mismatching hashes (Tampering Detected)
    print("Demo 2: Mismatching Hashes (Tampering Detected)")
    print("-" * 40)
    hash_post_tampered = hash_pre[:-1] + "X"  # Change last character

    result_tampered = verifyHash(hash_pre, hash_post_tampered)
    print(f"Hash pre:  {result_tampered['hash_pre']}")
    print(f"Hash post: {result_tampered['hash_post']}")
    print(f"Match: {result_tampered['match']}")
    print(f"Alert: {result_tampered['alert_level']}")
    print(f"Message: {result_tampered['message']}")
    print()

    # Demo 3: Explain timing attack prevention
    print("Why hmac.compare_digest():")
    print("-" * 40)
    print("Python's '==' operator returns early on mismatch:")
    print('  "abc" == "abxc"     -> Fast (mismatch at pos 3)')
    print('  "abc" == "abcd"     -> Slower (mismatch at pos 4)')
    print()
    print("An attacker can measure response times and brute-force hashes.")
    print()
    print("hmac.compare_digest() always takes the same time:")
    print('  hmac.compare_digest("abc", "abxc")  -> Same as below')
    print('  hmac.compare_digest("abc", "abcd")  -> Same time')
    print()
    print("This prevents timing attacks on hash comparisons.")
    print()

    print("=" * 60)
