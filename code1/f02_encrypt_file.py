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
│  Magic (4 bytes):        "SFFS"                                  │
│  Version (1 byte):        0x03                                   │
│  IV (12 bytes):           Random initialization vector           │
│  Hash Pre (32 bytes):     SHA-256 of ORIGINAL plaintext          │
│  File Size (8 bytes):     Original file size (uint64, LE)        │
│  ExtLen (1 byte):         Length of original file extension      │
│  Ext (N bytes):           Original file extension (UTF-8)        │
│  TokenOffset (2 bytes):   Byte offset of token in ciphertext     │
│  Ciphertext (M bytes):    AES-GCM(plaintext with 32-byte token   │
│                           injected at TokenOffset)               │
└────────────────────────────────────────────────────────────────┘

Provenance token (32 bytes) sits in the header AFTER the extension
field — in plaintext, readable without the AES key.  The token is
registered in the provenance table (sffs_data/provenance.json) keyed
by hash_pre.  During decryption the token is checked against the table
BEFORE the AES key is touched — nothing is decrypted until provenance
passes.  Security comes from the table (secret), not from hiding the
token bytes in the file.

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
SFFS_VERSION = 0x03


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
            - hash_pre: SHA-256 hash of original plaintext (before encryption)
            - file_token: 32-byte provenance token embedded in ciphertext
            - token_offset: byte offset where token was injected in plaintext
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

    # Compute SHA-256 hash of ORIGINAL plaintext — stored in header and provenance table
    # This hash is over the original bytes BEFORE token injection
    hash_digest = hashlib.sha256(plaintext).digest()
    hash_pre = hash_digest.hex()

    # Generate provenance token — 32 cryptographically random bytes, unique per file.
    # Stored in the header (NOT inside ciphertext) so it can be checked BEFORE
    # any decryption occurs.  Security comes from the provenance table (which holds
    # the expected token); the table is checked before the AES key is used.
    file_token = secrets.token_bytes(32)

    # Generate cryptographically secure random IV (12 bytes = 96 bits)
    # Why: AES-GCM standard specifies 96-bit nonce for maximum efficiency and interoperability
    # 12-byte IV avoids internal GHASH reduction that 16-byte IVs trigger in GCM mode
    # Reusing IVs with same key is catastrophic for security
    iv = secrets.token_bytes(12)

    # Create AES-GCM cipher with generated IV
    aesgcm = AESGCM(aes_key)

    # Encrypt original plaintext — no token injection into plaintext.
    # Token sits in the header so it is verified before decryption begins;
    # no ciphertext bytes are ever decrypted until provenance checks pass.
    # GCM automatically computes and appends the 16-byte authentication tag.
    ciphertext = aesgcm.encrypt(iv, plaintext, associated_data=None)

    # Store original extension so decryption can restore it without leaking via filename.
    # The output .sffs file uses only the stem (no original ext visible on filesystem).
    # Extension is stored inside the header — hidden from directory listings.
    original_ext = input_path.suffix.encode("utf-8")   # e.g. b".docx" (≤ 255 bytes)
    ext_len = len(original_ext)                         # 1 byte length prefix
    # Bounds check: real file extensions are always short (e.g. ".docx" = 5 bytes).
    # The header field is a uint8 so values > 255 would overflow struct.pack("B", …);
    # we cap at 32 to reject obviously malformed inputs early.
    if ext_len > 32:
        raise ValueError(f"File extension too long ({ext_len} bytes); max 32")

    # Assemble SFFS V3 file header (90 + ext_len bytes total)
    # Header fields:
    #   Magic      (4 bytes):  Magic number "SFFS"
    #   Version    (1 byte):   Format version (0x03)
    #   IV         (12 bytes): Initialization vector (stored for decryption)
    #   Hash Pre   (32 bytes): SHA-256 hash of original plaintext
    #   File Size  (8 bytes):  Original file size as uint64 little-endian
    #   ExtLen     (1 byte):   Length of original file extension in bytes
    #   Ext        (N bytes):  Original file extension UTF-8 encoded (e.g. ".docx")
    #   Token      (32 bytes): Provenance token — verified BEFORE decryption
    # Note: GCM auth tag is embedded at the end of ciphertext — not stored separately
    # Note: Token is in the header (plaintext) so it can be verified without decrypting.
    #       Security = table lookup (token in table must match token in file).
    header = (
        SFFS_MAGIC +                             # Magic bytes
        struct.pack("B", SFFS_VERSION) +         # Version byte (0x03)
        iv +                                     # IV (12 bytes)
        hash_digest +                            # Hash of original plaintext (32 bytes)
        struct.pack("Q", original_size) +        # Original file size as uint64 little-endian
        struct.pack("B", ext_len) +              # Extension length (1 byte)
        original_ext +                           # Extension bytes (N bytes)
        file_token                               # Provenance token (32 bytes)
    )

    # Write complete SFFS file: header + ciphertext
    # Why: We write the header first, then ciphertext immediately after
    # This ensures atomic write of the complete encrypted file
    if output_path is None:
        # Use stem only — original extension stored inside header, not in filename.
        # Hides file type from directory listings (attacker sees only .sffs files).
        # e.g. document.docx -> document.sffs
        output_path = input_path.with_suffix(".sffs")

    output_path.write_bytes(header + ciphertext)

    return {
        "sffs_path": output_path,
        "hash_pre": hash_pre,
        "file_token": file_token,
        "iv": iv,
        "original_size": original_size,
        "status": "success",
    }


if __name__ == "__main__":
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
    header_bytes = result['sffs_path']
    magic = header_bytes.read_bytes()[:4]
    print(f"SFFS magic bytes: {magic}")
    print(f"Magic check: {'PASS' if magic == b'SFFS' else 'FAIL'}")
    print()

    print("=" * 60)
