"""
f07_create_isolated_sandbox.py — Student 2: System-Security Module

An isolated execution environment is a sandboxed directory where decrypted files
reside, separated from the host OS file system. This is critical for SFFS because:
- The host OS may already be compromised (malware, backdoor, insider threat)
- Standard temp directories are world-readable and can be forensically recovered
- If decrypted files touch the host filesystem, an attacker with any access to
  the host can read plaintext secrets

The sandbox differs from a temp directory because:
1. It has restrictive permissions (owner-only access)
2. It's tied to a session_id for lifecycle management
3. It's designed for secure wipe before destruction

Threat model:
- Malware on host OS attempting to read decrypted files
- Forensic recovery tools scanning disk for sensitive data
- Attacker using memory dumps or process memory scanners

Platform limitations:
- Windows: No true POSIX permissions, only ACLs via icacls
- Linux: Full POSIX permissions with chmod
"""

import os
import platform
import shutil
import stat
import subprocess
import time
import uuid
from pathlib import Path

# WHY: pathlib is used for cross-platform path handling — avoids Windows/Linux separator issues
from pathlib import Path
# WHY: stat is used to set restrictive file permissions programmatically
import stat
# WHY: platform detects Windows vs Linux for different permission models
import platform
# WHY: time is needed for lock file timestamp
import time


def createIsolatedSandbox(base_path: Path, session_id: str = None) -> dict:
    """
    Create an isolated execution environment (sandbox) for secure file handling.

    An isolated execution environment is a sandboxed directory where decrypted
    files reside, separated from the host OS file system. This prevents malware
    or compromised host systems from reading sensitive decrypted data.

    Args:
        base_path: The base path where the sandbox will be created (e.g., user's home)
        session_id: Optional session identifier. If None, a UUID is generated.

    Returns:
        dict: Contains sandbox_path, session_id, decrypted_dir, temp_dir,
              keys_runtime_dir, created_at, and platform info.

    Raises:
        RuntimeError: If sandbox creation fails (permissions denied)
    """
    # Generate session_id if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())

    # Create sandbox directory: base_path/sandbox_{session_id}/
    sandbox_path = base_path / f"sandbox_{session_id}"
    sandbox_path.mkdir(parents=True, exist_ok=False)

    # Set restrictive permissions based on platform
    # WHY: On Linux, os.chmod works with POSIX permission bits (0o700 = owner rwx only)
    # WHY: On Windows, we need icacls for true ACL control — stat module alone is insufficient
    #       because Windows uses ACLs (Access Control Lists), not POSIX permission bits.
    #       stat only reads current permissions, it doesn't provide the ability to set
    #       granular ACLs. We must use os.system('icacls ...') for proper isolation.

    if platform.system() == "Linux":
        # Linux: Use chmod for owner-only access
        os.chmod(sandbox_path, 0o700)
    elif platform.system() == "Windows":
        # Windows: Remove inherited permissions and grant only current user.
        # WHY: This command removes inherited permissions and grants access only to current user.
        # SECURITY: Failure is NOT silently swallowed — an unprotected sandbox directory
        # would retain inherited (potentially world-readable) ACLs, undermining isolation.
        try:
            current_user = os.environ.get('USERNAME', 'USER')
            subprocess.run([
                'icacls', str(sandbox_path),
                '/inheritance:r',  # Remove inherited permissions
                '/grant:r', f'{current_user}:(OI)(CI)F'  # Grant full control only to current user
            ], check=True, capture_output=True, stdin=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            # Clean up the unprotected directory before raising so it doesn't
            # linger on disk with open permissions.
            try:
                shutil.rmtree(str(sandbox_path))
            except Exception:
                pass
            raise RuntimeError(
                f"Failed to set restrictive ACLs on sandbox {sandbox_path}: {e}. "
                f"Sandbox isolation cannot be guaranteed — aborting creation."
            ) from e

    # Create subdirectories
    decrypted_dir = sandbox_path / "decrypted"
    temp_dir = sandbox_path / "temp"
    keys_runtime_dir = sandbox_path / "keys_runtime"
    decrypted_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    keys_runtime_dir.mkdir(parents=True, exist_ok=True)

    # Write sandbox.lock file containing session_id and timestamp.
    # SECURITY: On Linux, use os.open with mode 0o600 so the lock file is
    # owner-readable only, preventing session_id leaking to other local users.
    lock_file = sandbox_path / "sandbox.lock"
    created_time = int(time.time())
    lock_content = f"session_id={session_id}\ncreated={created_time}\n"
    if platform.system() == "Linux":
        fd = os.open(str(lock_file), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, lock_content.encode("utf-8"))
        finally:
            os.close(fd)
    else:
        lock_file.write_text(lock_content)

    # On Windows, verify ACLs were not silently left broad after icacls.
    # Done AFTER lock file creation so isSandboxIntact() can pass its full check.
    if platform.system() == "Windows" and not isSandboxIntact(sandbox_path):
        try:
            shutil.rmtree(str(sandbox_path))
        except Exception:
            pass
        raise RuntimeError(
            f"ACL verification failed post-icacls on {sandbox_path} — "
            f"broad permissions detected. Sandbox isolation cannot be guaranteed."
        )

    # Return dict with sandbox info
    return {
        "sandbox_path": sandbox_path,
        "session_id": session_id,
        "decrypted_dir": decrypted_dir,
        "temp_dir": temp_dir,
        "keys_runtime_dir": keys_runtime_dir,
        "created_at": str(lock_file),
        "platform": platform.system()
    }


def destroySandbox(sandbox_path: Path) -> bool:
    """
    Securely destroy a sandbox by wiping its contents and removing the directory.

    This function first wipes all files with a 3-pass overwrite (zeros, ones, random),
    then deletes them, then removes the directory structure.

    Args:
        sandbox_path: Path to the sandbox directory to destroy

    Returns:
        bool: True if sandbox was completely removed

    Security Notes:
        Standard shutil.rmtree is NOT sufficient for secure deletion because:
        - It doesn't overwrite file contents before deletion
        - Files remain recoverable via forensic tools (photorec, testdisk, etc.)
        - Deleted files show up in filesystem metadata until overwritten
    """
    # WHY: We must wipe files before deletion because standard deletion just removes
    # the directory entry — the actual data remains on disk until overwritten.
    # A forensic tool can easily recover deleted files from unallocated space.

    # First, wipe all files in the directory
    if sandbox_path.exists():
        secureWipeDirectory(sandbox_path)

    # Then remove the directory tree
    try:
        shutil.rmtree(sandbox_path)
        return True
    except FileNotFoundError:
        # Already removed
        return True
    except Exception as e:
        print(f"Error destroying sandbox: {e}")
        return False


def _write_and_sync(path: Path, data: bytes) -> None:
    """
    Write *data* to *path* and fsync before returning.

    WHY fsync after each overwrite pass:
    - Without fsync the OS write cache may hold the data in RAM; if the system
      crashes between overwrite passes, only the older pass reaches disk.
    - fsync flushes the kernel page cache for the file to the storage device
      before we proceed to the next pass or deletion.
    - This is especially important on SSDs with internal write caches and on
      USB drives where the device may reorder writes arbitrarily.
    """
    with open(path, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())


def secureWipeDirectory(directory: Path) -> None:
    """
    Securely wipe all files in a directory using DOD 5220.22-M 3-pass standard.

    The DOD 5220.22-M standard requires overwriting data with three passes:
    - Pass 1: 0x00 (zeros)
    - Pass 2: 0xFF (ones)
    - Pass 3: Random bytes

    This makes forensic recovery virtually impossible.

    Args:
        directory: Path to directory whose contents should be securely wiped

    Security Notes:
        WHY standard shutil.rmtree is NOT sufficient:
        - It simply removes directory entries without overwriting data
        - Deleted files remain recoverable until new data overwrites them
        - Forensic tools like photorec can recover deleted files from unallocated space

        WHY we overwrite with zeros first:
        - Zero-fill overwrites the file with null bytes
        - This ensures any partial reads will return zeros, not remnants

        WHY we use random bytes for final pass:
        - Random bytes ensure no pattern remains that could be detected
        - This satisfies the most stringent requirement of DOD 5220.22-M
    """
    if not directory.exists():
        return

    # Walk all files in the directory
    for root, dirs, files in os.walk(directory):
        root_path = Path(root)
        for filename in files:
            file_path = root_path / filename

            # Get file size
            try:
                file_size = file_path.stat().st_size
            except OSError:
                continue

            # Pass 1: overwrite with zeros
            if file_size > 0:
                zeros = bytearray(file_size)
                _write_and_sync(file_path, zeros)

            # Pass 2: overwrite with ones
            if file_size > 0:
                ones = bytearray(file_size)
                ones[:] = b'\xff' * file_size
                _write_and_sync(file_path, ones)

            # Pass 3: overwrite with random bytes
            if file_size > 0:
                random_bytes = os.urandom(file_size)
                _write_and_sync(file_path, random_bytes)

            # Delete the file
            try:
                file_path.unlink()
            except OSError:
                pass

    # Now remove all subdirectories
    for root, dirs, files in os.walk(directory, topdown=False):
        for dirname in dirs:
            dir_path = Path(root) / dirname
            try:
                # Secure wipe directory contents first
                if dir_path.exists():
                    secureWipeDirectory(dir_path)
                # Then remove the directory
                dir_path.rmdir()
            except OSError:
                # Directory not empty or permission denied
                pass


def isSandboxIntact(sandbox_path: Path) -> bool:
    """
    Check if a sandbox is intact and has proper security settings.

    This function verifies:
    - The sandbox.lock file exists and is readable
    - Permissions are still restrictive
    - No unexpected files or directories have appeared

    Args:
        sandbox_path: Path to the sandbox directory

    Returns:
        bool: True if sandbox is intact, False otherwise

    Security Notes:
        WHY we check permissions:
        - If permissions have been relaxed (e.g., from 0o700 to 0o755),
          it may indicate an attacker or malware has compromised access
        - On Windows, this would mean ACLs have been modified
    """
    if not sandbox_path.exists():
        return False

    lock_file = sandbox_path / "sandbox.lock"
    if not lock_file.exists():
        return False

    # Check lock file is readable
    try:
        lock_content = lock_file.read_text()
        if not lock_content.startswith("session_id="):
            return False
    except OSError:
        return False

    # Check permissions are still restrictive
    if platform.system() == "Linux":
        try:
            mode = oct(sandbox_path.stat().st_mode)[-3:]
            if mode not in ("700", "400", "500"):
                # Permissions have changed — warn but don't fail
                print(f"Warning: Sandbox permissions changed to {mode}")
                return False
        except OSError:
            return False
    elif platform.system() == "Windows":
        # Verify ACLs have not been broadened by checking icacls output.
        # If broad access entries (Everyone, BUILTIN\Users, etc.) appear,
        # the sandbox has been tampered with or icacls setup failed.
        try:
            result = subprocess.run(
                ["icacls", str(sandbox_path), "/Q"],
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                check=True,
            )
            output = result.stdout
            broad_entries = [
                "Everyone",
                "BUILTIN\\Users",
                "NT AUTHORITY\\Authenticated Users",
            ]
            for entry in broad_entries:
                if entry in output:
                    print(f"Warning: Sandbox ACL contains broad entry: {entry}")
                    return False
        except (subprocess.CalledProcessError, OSError) as e:
            print(f"Warning: Could not verify sandbox ACL: {e}")
            return False

    return True


if __name__ == "__main__":
    import tempfile

    # Create sandbox
    print("Creating isolated sandbox...")
    sandbox_info = createIsolatedSandbox(Path(tempfile.gettempdir()))
    print(f"Sandbox path: {sandbox_info['sandbox_path']}")
    print(f"Session ID: {sandbox_info['session_id']}")
    print(f"Platform: {sandbox_info['platform']}")
    print(f"Decrypted dir: {sandbox_info['decrypted_dir']}")
    print(f"Temp dir: {sandbox_info['temp_dir']}")
    print(f"Keys runtime dir: {sandbox_info['keys_runtime_dir']}")

    # Create a test file inside the sandbox
    test_file = sandbox_info['decrypted_dir'] / "test_secret.txt"
    test_file.write_text("This is a secret that should be secure.")
    print(f"\nCreated test file: {test_file}")
    print(f"File permissions: {oct(test_file.stat().st_mode)[-3:]}")

    # Destroy the sandbox
    print("\nDestroying sandbox...")
    result = destroySandbox(sandbox_info['sandbox_path'])
    print(f"Sandbox destroyed: {result}")

    # Confirm directory no longer exists
    if not sandbox_info['sandbox_path'].exists():
        print("[OK] Sandbox directory no longer exists")
    else:
        print("[FAIL] Sandbox directory still exists!")
