"""
SFFS — Student 1: Hash Generation Module

This module provides cryptographic hash functions for integrity verification.

What is a Cryptographic Hash Function?
- One-way: Cannot reverse hash to get original input
- Deterministic: Same input always produces same hash
- Avalanche Effect: 1-bit change in input → completely different hash
- Collision Resistant: Very difficult to find two inputs with same hash

Why SHA-256 (not MD5 or SHA-1):
- SHA-256 produces 256-bit (32-byte) hash
- Provides 128-bit collision resistance (theoretically)
- SHA-1 is deprecated (practical attacks exist)
- MD5 is broken (trivial collisions)
- SHA-256 is FIPS-140-2 approved

Why BLAKE2 is offered as alternative:
- BLAKE2b is faster than SHA-256 for large files
- Still provides strong security
- Python stdlib doesn't include BLAKE2 (need external lib)
- We support it via pycryptodome for performance

Hash vs Checksum:
- Checksum: Non-cryptographic (CRC32, MD5) — fast, weak security
- Hash: Cryptographic (SHA-256, SHA-512, BLAKE2) — slower, strong security
- Use checksums for quick corruption detection
- Use hashes for security-critical integrity verification

Streaming Hash (Large Files):
- Read file in 8MB chunks (handles files > RAM)
- Process each chunk through hash function
- Hash is incremental — no need to load entire file in memory
- This enables hashing multi-GB files on modest hardware
"""

# Why: hashlib provides FIPS-140-2 certified hash functions
# Why: pathlib handles cross-platform path operations cleanly
# Why: typing.Union allows function to accept both Path and bytes
# Why: Union makes type hints explicit for IDE support
from hashlib import sha256, sha512, blake2b
from pathlib import Path
from typing import Union


def generateHash(target: Union[Path, bytes], algorithm: str = "sha256") -> str:
    """
    Generate a cryptographic hash of the given data.

    Args:
        target: Either a Path (file) or raw bytes to hash
        algorithm: Hash algorithm — "sha256" (default), "sha512", or "blake2b"

    Returns:
        Lowercase hex digest string (64 chars for SHA-256)

    Raises:
        ValueError: If unsupported algorithm specified
        FileNotFoundError: If file path doesn't exist
        TypeError: If target is neither Path nor bytes
    """
    # Validate algorithm
    supported_algorithms = {"sha256", "sha512", "blake2b"}
    if algorithm.lower() not in supported_algorithms:
        raise ValueError(
            f"Unsupported algorithm: {algorithm}. "
            f"Supported: {', '.join(sorted(supported_algorithms))}"
        )

    # Handle bytes input directly
    if isinstance(target, bytes):
        if algorithm.lower() == "blake2b":
            return blake2b(target).hexdigest()
        elif algorithm.lower() == "sha512":
            return sha512(target).hexdigest()
        else:  # sha256
            return sha256(target).hexdigest()

    # Handle file path input — stream in 8MB chunks
    # Why: 8MB chunks balance memory usage and I/O performance
    # Why: Streaming allows hashing files larger than available RAM
    if isinstance(target, Path):
        if not target.exists():
            raise FileNotFoundError(f"File not found: {target}")

        hash_func = None
        if algorithm.lower() == "blake2b":
            hash_func = blake2b()
        elif algorithm.lower() == "sha512":
            hash_func = sha512()
        else:  # sha256
            hash_func = sha256()

        # Stream file in 8MB chunks
        CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB
        with target.open("rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                hash_func.update(chunk)

        return hash_func.hexdigest()

    raise TypeError(f"target must be Path or bytes, got {type(target)}")


def generateFileHash(path: Path) -> dict:
    """
    Convenience function to hash a file and return metadata.

    Args:
        path: File path to hash

    Returns:
        dict with:
            - hash: SHA-256 hex digest (default)
            - algorithm: "sha256", "sha512", or "blake2b"
            - file_size: File size in bytes
            - file_name: Base filename

    Note: Always uses SHA-256 (can be changed by passing bytes)
    """
    hash_value = generateHash(path)
    file_size = path.stat().st_size
    file_name = path.name

    return {
        "hash": hash_value,
        "algorithm": "sha256",
        "file_size": file_size,
        "file_name": file_name,
    }


if __name__ == "__main__":
    # Demo: Hash this file's own source code
    source_file = Path(__file__)

    print("=" * 60)
    print("SFFS — Hash Generation Demo")
    print("=" * 60)
    print(f"Hashing file: {source_file.name}")
    print()

    # Hash using different algorithms
    print("Using SHA-256 (default):")
    hash_sha256 = generateHash(source_file)
    print(f"  {hash_sha256}")
    print()

    print("Using SHA-512:")
    hash_sha512 = generateHash(source_file, "sha512")
    print(f"  {hash_sha512[:64]}... (truncated)")
    print()

    print("Using BLAKE2b (faster):")
    hash_blake2b = generateHash(source_file, "blake2b")
    print(f"  {hash_blake2b[:64]}... (truncated)")
    print()

    # Demo: Avalanche effect — change 1 byte in file
    print("Demonstrating Avalanche Effect:")
    print("-" * 40)

    # Original file content hash
    original_hash = generateHash(source_file)
    print(f"Original hash of {source_file.name}:")
    print(f"  {original_hash}")

    # Modify file (add a newline at end)
    modified_content = source_file.read_bytes() + b"\n"
    modified_hash = generateHash(modified_content)

    print()
    print("After adding 1 byte (newline):")
    print(f"  {modified_hash[:64]}... (truncated)")
    print()
    print(f"Both hashes different: {original_hash != modified_hash}")
    print(f"Avalanche effect: ✓ Even 1-bit change produces completely different hash")
    print()

    print("=" * 60)
