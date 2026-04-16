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
from f06_secure_key_storage import secureKeyStorage, wrapAESKey
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

    def initialize(self) -> dict:
        self.paths = initDriveDetection()
        cfg_dir = self.paths["config_dir"]
        self.config = configLoader("load", cfg_dir, encryption_key=None)
        self._auth_db = self.paths["data_dir"] / "auth.db"
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
        pub = keys_dir / "public_key.pem"
        if not pub.exists():
            g = generateKeyPairs(keys_dir, key_size=2048)
            secureKeyStorage(g["private_key_bytes"], master_password, keys_dir)
            pub = g["public_key_path"]
        return pub

    def encryptFileOperation(self, input_path: Path, master_password: str | None = None) -> dict:
        self._require_session()
        assert self.paths and self.logger
        if master_password is None:
            master_password = self._master_password_str()
        input_path = Path(input_path)
        pub = self._ensure_rsa_keys(master_password)
        aes_key = session_random_bytes(32)
        out_sffs = input_path.with_suffix(".sffs")
        enc = encryptFile(input_path, aes_key, out_sffs)
        wrapped = wrapAESKey(aes_key, pub)
        wrap_path = out_sffs.parent / f"{out_sffs.stem}.aeswrap"
        wrap_path.write_bytes(wrapped)
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
            "wrap_path": wrap_path,
            "status": "encrypted",
        }

    def decryptFileOperation(self, sffs_path: Path, master_password: str | None = None) -> dict:
        self._require_session()
        assert self.paths and self.sandbox and self.logger
        if master_password is None:
            master_password = self._master_password_str()
        sffs_path = Path(sffs_path)
        wrap_path = sffs_path.parent / f"{sffs_path.stem}.aeswrap"
        if not wrap_path.exists():
            raise FileNotFoundError(f"Missing AES wrap file: {wrap_path}")
        ks = next(self.paths["keys_dir"].glob("keystore_*.json"), None)
        if ks is None:
            raise FileNotFoundError("No keystore in keys_dir")
        dec = self._decrypt_via_worker(
            sffs_path=sffs_path,
            wrap_path=wrap_path,
            keystore_path=ks,
            output_dir=Path(self.sandbox["decrypted_dir"]),
            sandbox_root=Path(self.sandbox["sandbox_path"]),
            master_password=master_password,
        )
        if self.logger:
            self.logger.log(
                f"Decrypt {sffs_path.name}",
                "INFO",
                module="SFFSCore",
                user_id=self._user_id,
                metadata={"out": str(dec["output_path"]), "via_worker": True},
            )
        out = Path(dec["output_path"])
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
        wrap_path: Path,
        keystore_path: Path,
        output_dir: Path,
        sandbox_root: Path,
        master_password: str,
    ) -> dict:
        payload = {
            "sffs_path": str(sffs_path),
            "wrap_path": str(wrap_path),
            "keystore_path": str(keystore_path),
            "output_dir": str(output_dir),
            "sandbox_root": str(sandbox_root),
            "master_password": master_password,
        }
        envelope = self._sign_worker_payload(payload)
        proc = subprocess.Popen(
            [
                sys.executable,
                str(self._worker_script),
                "--action",
                "decrypt",
                "--payload",
                json.dumps(envelope),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={
                **os.environ,
                "SFFS_IPC_KEY": self._ipc_secret,
                "SFFS_WORKER_POLICY": str(self._worker_policy),
            },
        )
        with self._workers_lock:
            self._active_workers[proc.pid] = proc
        try:
            stdout, stderr = proc.communicate(timeout=60)
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
        if self.process_monitor:
            try:
                self.process_monitor.stop()
            except Exception:
                pass
