# SFFS — Phase 1: Student 1 — Crypto-Security Module

You are building the SFFS (Smart File Fortify System). This is Phase 1: write all 6 cryptographic function files for Student 1.

**Assume Phase 0 is complete.** All directories exist. Work inside the `code1/` folder.

---

## Context

Student 1 owns all mathematical security: AES-256 encryption/decryption, RSA-2048 key management, SHA-256 hashing and integrity verification. Every file must be independently runnable and also importable by the main system.

The output encrypted file format is `.sffs` — a custom binary format with this header:

```
[4 bytes]  Magic number: b'SFFS'
[1 byte]   Version: 0x01
[16 bytes] AES-GCM IV (Initialization Vector)
[16 bytes] AES-GCM Auth Tag
[32 bytes] SHA-256 hash of original plaintext (pre-encryption)
[8 bytes]  Original file size (uint64, little-endian)
[N bytes]  Ciphertext
```

---

## Files to Create

---

### `code1/f01_generate_key_pairs.py`

**Function:** `generateKeyPairs(output_dir, key_size=2048)`

Write a complete, production-quality Python file that:

1. **Imports** (with a comment explaining WHY each is chosen):
   - `from Crypto.PublicKey import RSA` — pycryptodome, fastest RSA in Python
   - `from cryptography.hazmat.primitives.serialization import ...` — for PEM encoding
   - `pathlib.Path`, `os`, `secrets`, `datetime`

2. **Module docstring** at the top explaining:
   - What RSA is and why 2048-bit minimum is the industry standard
   - Why the private key must NEVER be stored in plain text
   - How this function fits into the SFFS key lifecycle

3. **Function `generateKeyPairs(output_dir: Path, key_size: int = 2048) -> dict`:**
   - Generate RSA key pair using `pycryptodome`
   - Export public key as `public_key.pem` (unencrypted, safe to share)
   - Export private key as raw bytes — DO NOT write to disk directly
   - Return dict: `{"public_key_path": Path, "private_key_bytes": bytes, "key_id": str, "generated_at": str}`
   - `key_id` = first 8 chars of SHA-256 of the public key
   - Add detailed inline comments explaining each step
   - Raise `ValueError` if key_size < 2048

4. **`if __name__ == "__main__":` demo block** that:
   - Creates keys in a `./code1/test_output/` directory
   - Prints key_id and confirms public_key.pem exists
   - Shows the first 5 lines of the public key
   - Explicitly states: "Private key bytes NOT written to disk — pass to secureKeyStorage()"

---

### `code1/f02_encrypt_file.py`

**Function:** `encryptFile(input_path, aes_key, output_path=None) -> dict`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `from Crypto.Cipher import AES` — AES-GCM implementation
   - `from Crypto.Random import get_random_bytes` — cryptographically secure random
   - `pathlib`, `struct`, `hashlib`, `os`

2. **Module docstring** explaining:
   - Why AES-256-GCM (not CBC): GCM provides both encryption AND authentication in one pass
   - What an IV is and why it must be random for every encryption operation
   - What the GCM auth tag is and why it prevents ciphertext tampering
   - The complete `.sffs` file format (all fields, sizes, and purpose of each)

3. **Function `encryptFile(input_path: Path, aes_key: bytes, output_path: Path = None) -> dict`:**
   - Validate: `aes_key` must be exactly 32 bytes (256 bits)
   - Read input file bytes
   - Compute SHA-256 hash of plaintext BEFORE encryption (call `generateHash` inline)
   - Generate 16-byte random IV using `get_random_bytes`
   - Encrypt using AES-256-GCM
   - Write `.sffs` file with full header (magic, version, IV, auth_tag, hash, filesize, ciphertext)
   - If `output_path` is None, use `input_path.with_suffix('.sffs')`
   - Return dict: `{"sffs_path": Path, "hash_pre": str, "iv": bytes, "original_size": int, "status": "success"}`
   - Raise `ValueError` on wrong key size
   - Raise `FileNotFoundError` if input doesn't exist

4. **`if __name__ == "__main__":` demo:**
   - Creates a test file `./code1/test_output/sample.txt` with `"Hello SFFS! This is a test file."` content
   - Generates a random 32-byte key
   - Encrypts to `sample.sffs`
   - Prints the `.sffs` file size and confirms `.sffs` header magic bytes

---

### `code1/f03_decrypt_file.py`

**Function:** `decryptFile(sffs_path, aes_key, output_dir=None) -> dict`

Write a complete Python file that:

1. **Imports with WHY comments** (same crypto imports as f02)

2. **Module docstring** explaining:
   - Why GCM auth tag is verified BEFORE decryption begins (fail-fast on tampered files)
   - Why output is restricted to an isolated directory (never host OS disk)
   - The security risk if decrypted files touch the host file system

3. **Function `decryptFile(sffs_path: Path, aes_key: bytes, output_dir: Path = None) -> dict`:**
   - Read and parse the `.sffs` header (validate magic bytes = `b'SFFS'`)
   - Extract IV, auth_tag, hash_pre, original_size from header
   - Verify AES-GCM auth tag — if invalid, raise `SecurityError` (define this custom exception) with message "File tampered or corrupted — decryption aborted"
   - Decrypt ciphertext
   - Write decrypted output to `output_dir` (or same directory as `.sffs` if None)
   - Compute SHA-256 of decrypted output (hash_post)
   - Return dict: `{"output_path": Path, "hash_pre": str, "hash_post": str, "original_size": int, "status": "success"}`
   - On auth tag failure: delete any partial output and raise `SecurityError`

4. **Custom exception class** `SecurityError(Exception)` at top of file

5. **`if __name__ == "__main__":` demo** that decrypts the `sample.sffs` created by f02 and confirms the decrypted content matches the original

---

### `code1/f04_generate_hash.py`

**Function:** `generateHash(target, algorithm="sha256") -> str`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `hashlib` — stdlib, FIPS-140 certified implementations
   - `pathlib`, `typing`

2. **Module docstring** explaining:
   - What a cryptographic hash function is (one-way, deterministic, avalanche effect)
   - Why SHA-256 specifically (256-bit output, collision resistant, widely audited)
   - The difference between a hash and a checksum
   - Why BLAKE2 is offered as an alternative (faster for large files)

3. **Function `generateHash(target: Union[Path, bytes], algorithm: str = "sha256") -> str`:**
   - Accept either a `Path` (file) or raw `bytes`
   - If `Path`: read file in 8MB chunks (streaming — handles files larger than RAM)
   - If `bytes`: hash directly
   - Support algorithms: `"sha256"`, `"sha512"`, `"blake2b"`
   - Return lowercase hex digest string
   - Raise `ValueError` if unsupported algorithm
   - Raise `FileNotFoundError` if path doesn't exist

4. **Helper function `generateFileHash(path: Path) -> dict`** that returns:
   - `{"hash": str, "algorithm": str, "file_size": int, "file_name": str}`

5. **`if __name__ == "__main__":` demo** that hashes its own source file and demonstrates the avalanche effect (change 1 byte → completely different hash)

---

### `code1/f05_verify_hash.py`

**Function:** `verifyHash(hash_pre, hash_post) -> dict`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `hmac` — for constant-time comparison (prevents timing attacks)
   - `hashlib`, `pathlib`

2. **Module docstring** explaining:
   - What a timing attack is and why `==` is dangerous for hash comparison
   - Why `hmac.compare_digest()` is the correct comparison function
   - How `hash_pre` (before encryption) and `hash_post` (after decryption) prove file integrity
   - Real-world threat: a man-in-the-middle modifying an encrypted file

3. **Function `verifyHash(hash_pre: str, hash_post: str) -> dict`:**
   - Use `hmac.compare_digest()` for constant-time comparison
   - Return dict: `{"match": bool, "alert_level": str, "hash_pre": str, "hash_post": str, "message": str}`
   - If match: `alert_level = "OK"`, `message = "File integrity verified — no tampering detected"`
   - If mismatch: `alert_level = "CRITICAL_TAMPER_DETECTED"`, `message = "WARNING: File hash mismatch — file may have been tampered with"`

4. **Function `verifyFileIntegrity(original_path: Path, decrypted_path: Path) -> dict`:**
   - Convenience wrapper: hashes both files then calls `verifyHash()`
   - Returns same dict with additional `"original_path"` and `"decrypted_path"` fields

5. **`if __name__ == "__main__":` demo:**
   - Shows a passing verification (identical strings)
   - Shows a failing verification (one character different)
   - Demonstrates why a single-bit change is detected

---

### `code1/f06_secure_key_storage.py`

**Function:** `secureKeyStorage(private_key_bytes, master_password, output_dir) -> dict`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `from Crypto.Cipher import AES` — to encrypt the private key before storage
   - `from Crypto.Protocol.KDF import PBKDF2` — key derivation from password
   - `from Crypto.Hash import SHA256, HMAC` — for KDF PRF
   - `from Crypto.Random import get_random_bytes`
   - `from Crypto.PublicKey import RSA`
   - `pathlib`, `json`, `base64`, `struct`

2. **Module docstring** explaining:
   - Why the RSA private key is the most sensitive asset in the entire system
   - What PBKDF2 is: Password-Based Key Derivation Function 2 — turns a weak password into a strong cryptographic key
   - Why 310,000 iterations (NIST 2023 recommendation for SHA-256)
   - Why a salt is required (prevents rainbow table attacks)
   - How AES-256-GCM wraps the private key (key-wrapping)
   - The key store file format (JSON with base64-encoded fields)

3. **Function `secureKeyStorage(private_key_bytes: bytes, master_password: str, output_dir: Path, key_id: str = None) -> dict`:**
   - Generate 32-byte random salt
   - Derive 32-byte AES key from `master_password` using PBKDF2-SHA256 with 310,000 iterations
   - Encrypt `private_key_bytes` using AES-256-GCM
   - Write key store JSON to `output_dir/keystore_{key_id}.json` with fields:
     - `"version": "1.0"`
     - `"key_id": str`
     - `"kdf": "PBKDF2-SHA256"`
     - `"kdf_iterations": 310000`
     - `"salt": base64`
     - `"iv": base64`
     - `"auth_tag": base64`
     - `"encrypted_private_key": base64`
     - `"created_at": ISO timestamp`
   - IMMEDIATELY overwrite `private_key_bytes` in memory with zeros after encryption
   - Return dict: `{"keystore_path": Path, "key_id": str, "status": "stored"}`

4. **Function `retrieveKey(keystore_path: Path, master_password: str) -> bytes`:**
   - Load JSON keystore
   - Re-derive AES key from password + stored salt using same PBKDF2 parameters
   - Decrypt and return private key bytes
   - Wipe intermediate key material from memory
   - Raise `SecurityError` (import from f03) on wrong password (GCM auth tag fails)

5. **Function `wrapAESKey(aes_key: bytes, public_key_path: Path) -> bytes`:**
   - Encrypt an AES session key using RSA-OAEP with the public key
   - Returns encrypted AES key bytes (safe to store alongside .sffs file)

6. **Function `unwrapAESKey(encrypted_aes_key: bytes, keystore_path: Path, master_password: str) -> bytes`:**
   - Retrieve RSA private key via `retrieveKey()`
   - Decrypt the wrapped AES key using RSA-OAEP
   - Return raw AES key bytes

7. **`if __name__ == "__main__":` demo:**
   - Generates a fake 256-byte private key
   - Stores it with password `"TestPassword123!"`
   - Retrieves it and confirms bytes match
   - Shows that the keystore JSON contains ONLY base64-encoded ciphertext (no plain text key)
   - Demonstrates retrieval fails with wrong password

---

### `code1/run_student1.py`

Write an interactive demo runner that:

1. Has a text menu:
```
SFFS — Student 1: Crypto-Security Demo
======================================
[1] Generate RSA Key Pair
[2] Encrypt a file
[3] Decrypt a file
[4] Generate SHA-256 hash
[5] Verify file integrity
[6] Store & retrieve key securely
[7] Full end-to-end test (all functions)
[0] Exit
```

2. Option [7] runs a complete pipeline:
   - Generate RSA keys
   - Create a temp test file
   - Encrypt it
   - Tamper with the `.sffs` file (flip one byte in ciphertext area)
   - Attempt decryption → should raise SecurityError
   - Re-encrypt (no tamper)
   - Decrypt successfully
   - Verify hashes match
   - Store and retrieve key
   - Print a full report: PASS/FAIL for each step

3. Works on both Windows and Linux
4. All test files go into `./code1/test_output/` and are cleaned up at the end

---

### `code1/README.md`

Write a complete README covering:
- What this module does
- Prerequisites (Python 3.10+, pycryptodome, cryptography)
- How to install: `pip install pycryptodome cryptography`
- How to run: `python run_student1.py`
- Description of each function with its signature
- The `.sffs` file format specification (with ASCII diagram of header layout)
- Security notes: what algorithms are used and why
- How this module integrates with Student 2 and Student 3

---

## Rules for All Files

- Every import has an inline comment: `# Why: <reason this library was chosen>`
- Every function has a complete docstring: `Args:`, `Returns:`, `Raises:`, `Security Notes:`
- Inline comments explain the WHY, not the what (e.g., `# GCM mode chosen over CBC because it provides authentication — CBC only provides confidentiality`)
- Use `pathlib.Path` everywhere — never `os.path.join` with string slashes
- Every file is runnable standalone via `if __name__ == "__main__":`
- No hardcoded paths — use relative paths from a configurable base directory
- Handle both Windows and Linux path separators

## After All Files Created

Run this validation:
```bash
cd code1
python f01_generate_key_pairs.py
python f02_encrypt_file.py
python f03_decrypt_file.py
python f04_generate_hash.py
python f05_verify_hash.py
python f06_secure_key_storage.py
python run_student1.py  # select option 7
```

Confirm **Checkpoint 1 PASSED** — all 6 function files run cleanly, the end-to-end test in option 7 shows all steps PASS.
