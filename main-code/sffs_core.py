"""
sffs_core.py — SFFS Application Core

Orchestrates code1 (crypto), code2 (runtime security), and code3 (paths, config,
optional cloud). This module does not implement primitives; it sequences calls
and holds session state.

INITIALIZATION ORDER:
  1. initDriveDetection()
  2. configLoader(\"load\")
  3. initAuthDatabase()
  4. AuditLogger
  5. ProcessMonitor
  6. createIsolatedSandbox — after login only
  7. setupUSBRemovalDetection

SHUTDOWN: emergencyLock or graceful logout → destroySandbox → terminateSession → monitor stop.
"""

from __future__ import annotations

import base64
import secrets
import threading
import zipfile
import subprocess
import sys
import json
import hmac
import hashlib
import time
import os
from pathlib import Path
from typing import Any, Optional

from f01_generate_key_pairs import generateKeyPairs
from f02_encrypt_file import encryptFile
from f03_decrypt_file import SecurityError
from f04_generate_hash import generateHash
from f06_secure_key_storage import secureKeyStorage, wrapAESKey, verifyKeystorePassword
from wrap_store import WrapStore
from f07_create_isolated_sandbox import createIsolatedSandbox, destroySandbox
from f09_authenticate_user import authenticateUser, initAuthDatabase, terminateSession
from f10_monitor_process import ProcessMonitor
from f11_write_audit_log import AuditLogger
from f12_emergency_lock import emergencyLock, setupUSBRemovalDetection
from f13_init_drive_detection import initDriveDetection
from f08_secure_memory_wipe import secureMemoryWipe
from f16_cloud_sync import cloudSync
from f17_config_loader import configLoader
from mouse_entropy import session_random_bytes


class ConfigValidator:
    """
    Validate the SFFS path map before any crypto operations.

    WHY a separate class:
    - Startup misconfiguration (missing dirs, wrong permissions) causes
      confusing failures deep inside crypto modules.  Checking early gives
      a clear error message before any sensitive operation begins.
    """

    def validate(self, paths: dict) -> list[str]:
        """Return a list of error strings; empty list means all is well."""
        errors: list[str] = []
        for key in ("data_dir", "keys_dir", "sandbox_dir"):
            val = paths.get(key)
            if not val or not Path(val).exists():
                errors.append(f"Missing required path: {key} = {val!r}")
        auth_db = Path(paths.get("data_dir", ".")) / "auth.db"
        if auth_db.exists() and not os.access(auth_db, os.R_OK | os.W_OK):
            errors.append(f"auth.db is not readable/writable: {auth_db}")
        return errors


class SFFSCore:
    """Central orchestration for SFFS."""

    def __init__(self) -> None:
        self.paths: Optional[dict] = None
        self.config: Optional[dict] = None
        self.session_token: Optional[str] = None
        self.sandbox: Optional[dict] = None
        self.logger: Optional[AuditLogger] = None
        self.process_monitor: Optional[ProcessMonitor] = None
        self.usb_thread: Optional[threading.Thread] = None
        self.current_user: Optional[str] = None
        self._user_id: Optional[str] = None
        self._emergency_active = False
        self._auth_db: Optional[Path] = None
        # Login password copy — used for RSA keystore wrap/unwrap only during session
        self._session_password: Optional[bytearray] = None
        # .sffs resolved path -> last decrypted plaintext path in sandbox
        self._decrypt_cache: dict[str, Path] = {}
        self._worker_script = Path(__file__).resolve().parent / "isolated_worker.py"
        self._worker_policy = Path(__file__).resolve().parent / "worker_policy.json"
        self._ipc_secret = secrets.token_hex(32)
        self._ipc_counter = 0
        self._workers_lock = threading.Lock()
        self._active_workers: dict[int, subprocess.Popen] = {}
        self._viewers_lock = threading.Lock()
        self._active_viewers: set[int] = set()
        self._wrap_store: Optional[WrapStore] = None
        self._entropy_mode: str = "silent"

    def _derive_wrap_key(self, password: str) -> bytes:
        """Derive 32-byte AES key for WrapStore from session password + stored salt."""
        assert self.paths
        salt_path = self.paths["keys_dir"] / "wrap_store.salt"
        if not salt_path.exists():
            from Crypto.Random import get_random_bytes as _grb
            salt_path.write_bytes(_grb(16))
        salt = salt_path.read_bytes()
        from argon2.low_level import Type, hash_secret_raw
        return hash_secret_raw(
            secret=password.encode("utf-8"),
            salt=salt,
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            type=Type.ID,
        )

    def set_entropy_mode(self, mode: str) -> None:
        if mode not in ("silent", "interactive"):
            raise ValueError("Mode must be 'silent' or 'interactive'")
        self._entropy_mode = mode

    def initialize(self) -> dict:
        self.paths = initDriveDetection()
        cfg_dir = self.paths["config_dir"]
        self.config = configLoader("load", cfg_dir, encryption_key=None)
        self._auth_db = self.paths["data_dir"] / "auth.db"

        # Validate critical paths before any crypto operation.
        errs = ConfigValidator().validate(self.paths)
        if errs:
            raise RuntimeError("SFFS startup config errors:\n" + "\n".join(f"  • {e}" for e in errs))

        initAuthDatabase(self._auth_db)

        log_db = self.paths["logs_dir"] / "audit.db"
        self.logger = AuditLogger(log_db, encryption_key=None)

        self.process_monitor = ProcessMonitor(
            check_interval_ms=500,
            on_threat_detected_callback=self._on_threat_detected,
        )
        self.process_monitor.start()

        self.usb_thread = setupUSBRemovalDetection(
            self.paths["usb_root"], self._on_usb_removed
        )

        return {
            "status": "ready",
            "paths": self.paths,
            "platform": self.paths.get("platform"),
        }

    def _on_threat_detected(self, threat_type: str, details: str) -> None:
        self._terminate_active_workers()
        self._terminate_active_viewers()
        try:
            emergencyLock(
                "DEBUGGER_DETECTED",
                sandbox_path=Path(self.sandbox["sandbox_path"]) if self.sandbox else None,
                session_token=self.session_token,
                db_path=self._auth_db,
            )
        except SystemExit:
            raise
        except Exception:
            pass

    def _on_usb_removed(self, _reason: str = "USB_REMOVED") -> None:
        self._terminate_active_workers()
        self._terminate_active_viewers()
        try:
            emergencyLock(
                "USB_REMOVED",
                sandbox_path=Path(self.sandbox["sandbox_path"]) if self.sandbox else None,
                session_token=self.session_token,
                db_path=self._auth_db,
            )
        except SystemExit:
            raise
        except Exception:
            pass

    def login(self, username: str, password: bytearray) -> dict:
        assert self.paths and self._auth_db
        r = authenticateUser(username, password, self._auth_db)
        if r.get("authenticated"):
            self._session_password = bytearray(password)
            secureMemoryWipe(password)
            self.session_token = r.get("session_token")
            self._user_id = r.get("user_id")
            self.current_user = username
            sid = (self.session_token or secrets.token_hex(8))[:16]
            self.sandbox = createIsolatedSandbox(self.paths["sandbox_dir"], session_id=sid)
            self._decrypt_cache.clear()
            # WHY try/finally: if decode("utf-8") raises (e.g. the bytearray
            # contains non-UTF-8 bytes from an unusual password), the exception
            # propagates but _pw_str must still be cleaned up to avoid lingering
            # plaintext password on the stack.
            _pw_str = None
            try:
                _pw_str = self._session_password.decode("utf-8")
                wrap_key = self._derive_wrap_key(_pw_str)
            finally:
                del _pw_str
            wrap_db_path = self.paths["keys_dir"] / "wrap_store.db"
            self._wrap_store = WrapStore(wrap_db_path, wrap_key)
            self._wrap_store.initialize()
            if self.logger:
                self.logger.log(
                    "User login",
                    "INFO",
                    module="SFFSCore",
                    user_id=self._user_id,
                    metadata={"username": username},
                )
        return r

    def logout(self) -> None:
        self._terminate_active_workers()
        self._terminate_active_viewers()
        if self.session_token and self._auth_db:
            try:
                terminateSession(self.session_token, self._auth_db)
            except Exception:
                pass
        if self.sandbox:
            try:
                destroySandbox(Path(self.sandbox["sandbox_path"]))
            except Exception:
                pass
        if self._session_password is not None:
            secureMemoryWipe(self._session_password)
            self._session_password = None
        self._wrap_store = None
        self._decrypt_cache.clear()
        if self.logger:
            self.logger.log("User logout", "INFO", module="SFFSCore", user_id=self._user_id)
        self.session_token = None
        self.sandbox = None
        self.current_user = None
        self._user_id = None

    def _require_session(self) -> None:
        if not self.session_token or not self.sandbox:
            raise RuntimeError("No active session — login required.")

    def _master_password_str(self) -> str:
        if not self._session_password:
            raise RuntimeError("Session password not available — login again.")
        return self._session_password.decode("utf-8")

    def _ensure_rsa_keys(self, master_password: str) -> Path:
        assert self.paths
        keys_dir = self.paths["keys_dir"]
        # Find any public_key_<key_id>.pem (supports multiple keys, no silent overwrite)
        candidates = sorted(keys_dir.glob("public_key_*.pem"))
        pub = candidates[0] if candidates else None
        if pub is None:
            g = generateKeyPairs(keys_dir, key_size=2048)
            secureKeyStorage(g["private_key_bytes"], master_password, keys_dir)
            pub = g["public_key_path"]
        else:
            # Match keystore by key_id extracted from public key filename.
            # pub.stem = "public_key_<key_id>" → key_id = part after last "_"
            key_id = pub.stem.split("public_key_", 1)[-1]
            ks = keys_dir / f"keystore_{key_id}.json"
            if not ks.exists():
                # Fallback: pick first available keystore (legacy layout)
                ks = next(keys_dir.glob("keystore_*.json"), None)
            if ks:
                vr = verifyKeystorePassword(ks, master_password)
                if not vr["valid"]:
                    raise RuntimeError(
                        "Keystore was created with a different password. "
                        "Please log in with the original password used when "
                        "you first encrypted a file."
                    )
        return pub

    def encryptFileOperation(self, input_path: Path, master_password: str | None = None) -> dict:
        self._require_session()
        assert self.paths and self.logger
        if master_password is None:
            master_password = self._master_password_str()
        input_path = Path(input_path)
        pub = self._ensure_rsa_keys(master_password)
        if self._entropy_mode == "interactive":
            from mouse_entropy import is_entropy_ready
            if not is_entropy_ready():
                raise RuntimeError("INSUFFICIENT_ENTROPY")
        aes_key = session_random_bytes(32)
        # Stem only — original extension stored inside SFFS header, not in filename.
        # Hides file type from directory listings.
        out_sffs = input_path.with_suffix(".sffs")
        enc = encryptFile(input_path, aes_key, out_sffs)
        wrapped = wrapAESKey(aes_key, pub, bound_file_path=out_sffs)
        assert self._wrap_store is not None, "WrapStore not initialized — login required"
        self._wrap_store.store(out_sffs, wrapped, self._user_id)
        h = generateHash(input_path)
        if self.logger:
            self.logger.log(
                f"Encrypt {input_path.name}",
                "INFO",
                module="SFFSCore",
                user_id=self._user_id,
                metadata={"sffs": str(out_sffs)},
            )
        return {
            "sffs_path": out_sffs,
            "hash_pre": enc.get("hash_pre", h),
            "status": "encrypted",
        }

    def decryptFileOperation(
        self,
        sffs_path: Path,
        master_password: str | None = None,
        output_path: Path | None = None,
    ) -> dict:
        self._require_session()
        assert self.paths and self.sandbox and self.logger
        if master_password is None:
            master_password = self._master_password_str()
        sffs_path = Path(sffs_path)
        if output_path is not None:
            output_path = Path(output_path)
            if output_path.exists():
                raise FileExistsError(f"Output path already exists: {output_path}")
            output_dir = output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            sandbox_root = None
        else:
            output_dir = Path(self.sandbox["decrypted_dir"])
            sandbox_root = Path(self.sandbox["sandbox_path"])
        assert self._wrap_store is not None, "WrapStore not initialized — login required"
        wrap_data = self._wrap_store.lookup(sffs_path)
        ks = next(self.paths["keys_dir"].glob("keystore_*.json"), None)
        if ks is None:
            raise FileNotFoundError("No keystore in keys_dir")
        dec = self._decrypt_via_worker(
            sffs_path=sffs_path,
            wrap_data=wrap_data,
            keystore_path=ks,
            output_dir=output_dir,
            sandbox_root=sandbox_root,
            master_password=master_password,
        )
        out = Path(dec["output_path"])
        if output_path is not None and out != output_path:
            out.rename(output_path)
            out = output_path
        if self.logger:
            self.logger.log(
                f"Decrypt {sffs_path.name}",
                "INFO",
                module="SFFSCore",
                user_id=self._user_id,
                metadata={"out": str(out), "via_worker": True},
            )
        self._decrypt_cache[str(sffs_path.resolve())] = out
        return {
            "output_path": out,
            "integrity": "verified",
            "status": "decrypted",
        }

    def _decrypt_via_worker(
        self,
        *,
        sffs_path: Path,
        wrap_data: bytes,
        keystore_path: Path,
        output_dir: Path,
        sandbox_root: Path | None,
        master_password: str,
    ) -> dict:
        is_external = sandbox_root is None
        # SECURITY: master_password intentionally excluded from CLI payload.
        # It is passed via stdin pipe so it never appears in the process argument
        # list (visible via tasklist /V, /proc/<pid>/cmdline, or audit logs).
        payload = {
            "sffs_path": str(sffs_path),
            "wrap_data_b64": base64.b64encode(wrap_data).decode("ascii"),
            "keystore_path": str(keystore_path),
            "output_dir": str(output_dir),
            "sandbox_root": str(sandbox_root) if sandbox_root else "",
            "is_external_output": is_external,
        }
        envelope = self._sign_worker_payload(payload)
        _win_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        proc = subprocess.Popen(
            [
                sys.executable,
                str(self._worker_script),
                "--action",
                "decrypt",
                "--payload",
                json.dumps(envelope),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={
                **os.environ,
                "SFFS_IPC_KEY": self._ipc_secret,
                "SFFS_WORKER_POLICY": str(self._worker_policy),
            },
            creationflags=_win_flags,
        )
        with self._workers_lock:
            self._active_workers[proc.pid] = proc
        try:
            # master_password delivered via stdin — not in CLI args
            stdout, stderr = proc.communicate(
                input=master_password + "\n",
                timeout=60,
            )
        finally:
            with self._workers_lock:
                self._active_workers.pop(proc.pid, None)
        stdout = (stdout or "").strip()
        if not stdout:
            raise RuntimeError(f"Worker failed (no output), rc={proc.returncode}, stderr={stderr}")
        try:
            msg = json.loads(stdout.splitlines()[-1])
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Worker returned invalid JSON: {stdout}") from e
        if not msg.get("ok"):
            raise SecurityError(msg.get("error", "Worker decrypt failed"))
        return msg["result"]

    def _sign_worker_payload(self, payload: dict) -> dict:
        self._ipc_counter += 1
        nonce = f"{self._ipc_counter}:{secrets.token_hex(8)}"
        issued_at = int(time.time())
        envelope = {
            "payload": payload,
            "nonce": nonce,
            "session_token": self.session_token or "",
            "issued_at": issued_at,
        }
        msg = json.dumps(envelope, sort_keys=True, separators=(",", ":"))
        sig = hmac.new(self._ipc_secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()
        envelope["signature"] = sig
        return envelope

    def _terminate_active_workers(self) -> None:
        with self._workers_lock:
            workers = list(self._active_workers.values())
        for proc in workers:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    def register_external_viewer_pid(self, pid: int) -> None:
        """Track external viewer process PID for emergency shutdown."""
        if not isinstance(pid, int) or pid <= 0:
            return
        with self._viewers_lock:
            self._active_viewers.add(pid)

    def _terminate_active_viewers(self) -> None:
        """Best-effort termination of all tracked external viewer processes."""
        with self._viewers_lock:
            pids = list(self._active_viewers)
            self._active_viewers.clear()
        for pid in pids:
            try:
                proc = subprocess.Popen(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                )
                proc.wait(timeout=3)
            except Exception:
                # Fall back to os.kill for non-Windows or taskkill failures.
                try:
                    os.kill(pid, 15)
                except Exception:
                    pass

    def ensure_decrypted_for_view(self, sffs_path: Path) -> Path:
        """Decrypt if needed; reuse cached sandbox file when still present."""
        self._require_session()
        key = str(Path(sffs_path).resolve())
        if key in self._decrypt_cache:
            p = self._decrypt_cache[key]
            if p.exists():
                return p
        res = self.decryptFileOperation(Path(sffs_path))
        return Path(res["output_path"])

    def list_sandbox_files(self) -> list[Path]:
        """Decrypted files currently on disk under the session sandbox."""
        if not self.sandbox:
            return []
        d = Path(self.sandbox["decrypted_dir"])
        if not d.is_dir():
            return []
        return sorted([p for p in d.rglob("*") if p.is_file()])

    def backupKeys(self) -> dict:
        self._require_session()
        assert self.paths and self.config
        if not self.config.get("cloud_sync_enabled"):
            return {"status": "skipped", "message": "cloud_sync_enabled is false"}
        keys_dir = self.paths["keys_dir"]
        backup_zip = self.paths["backups_dir"] / "sffs_keys_backup.zip"
        with zipfile.ZipFile(backup_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in keys_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, arcname=f.relative_to(keys_dir))
        res = cloudSync(
            "upload",
            local_path=backup_zip,
            config_dir=self.paths["config_dir"],
        )
        if self.logger:
            self.logger.log("Cloud key backup", "INFO", module="SFFSCore", user_id=self._user_id)
        return res

    def shutdown(self) -> None:
        self._terminate_active_workers()
        self._terminate_active_viewers()
        if self.process_monitor:
            try:
                self.process_monitor.stop()
            except Exception:
                pass
