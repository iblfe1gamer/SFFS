# SFFS — Student 1: File Encryption Module

This module encrypts files using AES-256-GCM and writes them in the custom SFFS (.sffs) binary format.

## Requirements

- Python 3.8+
- `cryptography` package
- `pycryptodome` package

## Installation

```bash
pip install cryptography pycryptodome
```

## Usage

### Encrypt a file

```python
from pathlib import Path
from f02_encrypt_file import encryptFile

# Generate a random 32-byte AES key
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# For production, derive key from password using PBKDF2
# For demo/testing, use random bytes directly
import secrets
aes_key = secrets.token_bytes(32)

# Encrypt a file
input_file = Path("document.txt")
output_file = encryptFile(input_file, aes_key)

print(f"Encrypted to: {output_file['sffs_path']}")
print(f"Original file size: {output_file['original_size']} bytes")
```

### Encrypt with password-derived key

```python
from f02_encrypt_file import encryptFile
import secrets

# Derive key from password
password = b"YourStrongPassword123!"
salt = secrets.token_bytes(16)

kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=480000,
    backend=default_backend()
)

aes_key = kdf.derive(password.encode())

# Encrypt the file
result = encryptFile(input_file, aes_key)
```

### Decrypt a file

```python
from f02_decrypt_file import decryptFile

# Decrypt the file
decrypted_path = decryptFile("document.sffs", aes_key)

# Read decrypted content
content = decrypted_path.read_bytes()
print(content)
```

## SFFS File Format

The SFFS binary format structure:

```
┌─────────────────────────────────────────────────────────────────┐
│ Magic (4 bytes):   "SFFS"                                        │
│ Version (1 byte):   0x01                                         │
│ IV (16 bytes):     Random initialization vector                  │
│ Auth Tag (16 bytes): GCM authentication tag                      │
│ Hash Pre (32 bytes): SHA-256 of plaintext BEFORE encryption     │
│ File Size (8 bytes): Original file size (uint64, little-endian) │
│ Ciphertext (N bytes): Encrypted file content                     │
└─────────────────────────────────────────────────────────────────┘

Total header = 77 bytes before ciphertext.
```

## Security Notes

### Why AES-256-GCM?

- **Authenticated encryption**: GCM provides both confidentiality AND integrity in a single pass
- **No separate MAC needed**: CBC mode requires a separate Message Authentication Code
- **Tamper detection**: GCM's authentication tag detects any ciphertext tampering
- **Atomic verification**: GCM decrypts and verifies the tag atomically — fails if tag is invalid

### Initialization Vector (IV)

- Must be cryptographically random for EVERY encryption operation
- Same plaintext encrypted with different IVs produces different ciphertext
- IV does NOT need to be secret, but must be unpredictable
- Never reuse an IV with the same key

### Hash Before Encryption

- The SHA-256 hash proves the original plaintext integrity
- After decryption, we hash the plaintext again and compare
- Any tampering (even 1 bit) changes the hash completely (avalanche effect)
- Enables integrity verification without needing external signatures

## Testing

```bash
cd code1
.venv\Scripts\python.exe f02_encrypt_file.py
.venv\Scripts\python.exe f02_decrypt_file.py
```

## API

### `encryptFile(input_path, aes_key, output_path=None)`

Encrypt a file using AES-256-GCM.

**Args:**
- `input_path`: Path to the file to encrypt
- `aes_key`: AES encryption key (must be exactly 32 bytes)
- `output_path`: Optional output path. If None, uses `input_path.with_suffix('.sffs')`

**Returns:**
- `dict` with:
  - `sffs_path`: Path to the created .sffs file
  - `hash_pre`: SHA-256 hash of plaintext (before encryption)
  - `iv`: The IV used
  - `original_size`: Original file size in bytes
  - `status`: "success"

**Raises:**
- `ValueError`: If aes_key is not exactly 32 bytes
- `FileNotFoundError`: If input_path doesn't exist

### `decryptFile(sffs_path, aes_key)`

Decrypt a file from SFFS format.

**Args:**
- `sffs_path`: Path to the .sffs file to decrypt
- `aes_key`: AES encryption key (must be exactly 32 bytes)

**Returns:**
- `dict` with:
  - `plaintext_path`: Path to decrypted file
  - `plaintext`: Decrypted content as bytes
  - `hash_post`: SHA-256 hash of decrypted content
  - `hash_pre`: SHA-256 hash from SFFS header
  - `integrity_valid`: Boolean indicating if hashes match
  - `original_size`: Original file size in bytes
  - `status`: "success" or "error"

**Raises:**
- `ValueError`: If aes_key is not exactly 32 bytes
- `FileNotFoundError`: If sffs_path doesn't exist
- `FileIntegrityError`: If header magic bytes are invalid or integrity check fails

## License

MIT
