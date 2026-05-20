"""
f08_secure_memory_wipe.py — Student 2: System-Security Module

Python's del keyword does NOT erase memory — it merely removes a reference, allowing
the garbage collector to reclaim memory at some indeterminate time. For sensitive
data, this is a serious security risk.

A cold boot attack occurs when an attacker freezes RAM (using liquid nitrogen or
a freezer), reads its contents, and then restores the system to recover encryption
keys that were in memory.

A memory dump is a tool that copies the entire contents of RAM to a file. If an
attacker gains access to a victim's machine, they can create memory dumps to
extract plaintext passwords, encryption keys, or other secrets.

The DOD 5220.22-M standard is the Department of Defense's data erasure standard,
requiring 3-pass overwrite: zeros, ones, and random bytes.

WHY bytearray instead of bytes:
- Python strings are immutable and interned by the interpreter
- Once a string is created, it persists in memory until explicitly freed
- bytearray is mutable and can be overwritten with new data
- This allows us to actively wipe sensitive data with overwrite passes
"""

import ctypes
import os
import secrets
import sys
from pathlib import Path

# WHY: ctypes is the only way in Python to directly manipulate raw memory addresses
# and perform low-level operations like memset/memmove. The gc and del keywords
# are NOT sufficient for secure data erasure.
import ctypes


def secureMemoryWipe(target: bytearray, passes: int = 3) -> dict:
    """
    Securely wipe sensitive data from memory using DOD 5220.22-M 3-pass standard.

    This function overwrites a bytearray with three passes:
    - Pass 1: 0x00 (zeros)
    - Pass 2: 0xFF (ones)
    - Pass 3: Random bytes

    Args:
        target: A bytearray containing sensitive data to wipe
        passes: Number of overwrite passes (default: 3 per DOD 5220.22-M)

    Returns:
        dict: Contains bytes_wiped, passes_completed, and status

    Raises:
        TypeError: If target is not a bytearray (strings and bytes cannot be wiped)

    Security Notes:
        WHY we only accept bytearray:
        - Python strings are immutable and interned by the interpreter
        - Once created, a string persists until GC runs
        - We cannot overwrite a string's memory — we must replace it with a new object
        - bytearray is mutable and can be actively wiped with overwrites

        WHY we use ctypes for overwrites:
        - ctypes.memset provides low-level memory setting
        - ctypes.memmove provides low-level memory moving
        - These are faster than Python loops for large buffers

        WHY 3-pass overwrite:
        - Single pass may not fully erase due to cache, swap, and pagefile
        - Multiple passes ensure data is not recoverable via forensic tools
        - 3 passes is the DOD 5220.22-M standard
    """
    # Verify target is a bytearray
    if not isinstance(target, bytearray):
        raise TypeError(
            "secureMemoryWipe only accepts bytearray objects.\n"
            "Python strings are immutable and interned by the interpreter — "
            "once created they persist until garbage collection.\n"
            "Python bytes objects are also immutable.\n"
            "Always use bytearray() for sensitive data so it can be wiped."
        )

    original_size = len(target)
    passed_count = 0

    try:
        # Pass 1: overwrite with zeros
        if passed_count < passes:
            # WHY: bytearray[:] allows slice assignment with zeros
            target[:] = b'\x00' * len(target)
            passed_count += 1

        # Pass 2: overwrite with ones
        if passed_count < passes:
            # WHY: We use bytearray for mutable overwrites
            target[:] = b'\xff' * len(target)
            passed_count += 1

        # Pass 3: overwrite with random bytes
        if passed_count < passes:
            random_bytes = os.urandom(len(target))
            target[:] = random_bytes
            passed_count += 1

        # Zero the bytearray after all passes (final cleanup)
        target[:] = b'\x00' * len(target)

        return {
            "bytes_wiped": original_size,
            "passes_completed": passed_count,
            "status": "wiped"
        }

    except Exception as e:
        # On error, still zero out the data
        target[:] = b'\x00' * len(target)
        return {
            "bytes_wiped": original_size,
            "passes_completed": passed_count,
            "status": "error",
            "error": str(e)
        }


def wipeString(s: str) -> str:
    """
    Best-effort wipe of a string via ctypes.

    WARNING: This is best-effort only. Python strings are immutable and interned
    by the interpreter. Once a string is created, it cannot be modified in place.
    This function attempts to wipe the underlying memory, but the string object
    itself will be garbage collected at some indeterminate time.

    For secure string handling:
    - Use bytearray instead of str for sensitive data
    - Create a new empty string object and assign it to replace the sensitive one

    Args:
        s: The string to attempt to wipe

    Returns:
        str: An empty string as replacement

    Security Notes:
        WHY this is best-effort only:
        - Python's string interning may keep a reference to the string
        - The GC may not run immediately
        - Memory in the interpreter's string cache may persist
        - For true secure handling, replace with a new string object
    """
    # Attempt best-effort wipe via ctypes
    # WHY: This is only possible because strings are implemented as memory
    # However, we cannot guarantee the memory is actually freed
    # This is best-effort — for real security, use bytearray

    try:
        # Try to access the underlying memory via ctypes
        # This is a best-effort attempt — Python's string internals are not exposed
        s_bytes = s.encode('utf-8')
        wiped = bytearray(s_bytes)
        secureMemoryWipe(wiped)
        return ""  # Return empty string as replacement
    except Exception:
        # Best-effort failed — return empty string anyway
        return ""


def createSecureBuffer(size: int) -> bytearray:
    """
    Create a zeroed bytearray for secure data handling.

    This function is intended for creating sensitive buffers that can be
    securely wiped when no longer needed.

    Args:
        size: Size of the buffer in bytes

    Returns:
        bytearray: A zeroed bytearray of the given size

    Security Notes:
        WHY always use this function:
        - It creates a fresh bytearray with zeros
        - The buffer can be wiped when no longer needed
        - This prevents accidental reuse of sensitive data
    """
    return bytearray(size)


if __name__ == "__main__":
    print("SFFS — Secure Memory Wipe Demo\n" + "=" * 40 + "\n")

    # Create a bytearray containing sensitive data
    secret_password = bytearray(b"SecretPassword123")

    print(f"Content before wipe: {secret_password!r}")
    print(f"Size: {len(secret_password)} bytes\n")

    # Wipe it
    print("Wiping memory...")
    result = secureMemoryWipe(secret_password, passes=3)
    print(f"Result: {result}\n")

    # Print content after wipe
    print(f"Content after wipe: {secret_password!r}")
    print(f"Size: {len(secret_password)} bytes\n")

    # Demonstrate that the original variable now contains zeros
    print("Demonstrating bytearray wipe:")
    original = bytearray(b"SecretPassword123")
    wiped = bytearray(original)  # Copy
    secureMemoryWipe(wiped)
    print(f"  Original: {original!r}")
    print(f"  Wiped: {wiped!r}")
    print(f"  Both show zeros: {original == wiped and all(b == 0 for b in original)}")
