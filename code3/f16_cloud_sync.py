"""
f16_cloud_sync.py — SFFS Student 3: Google Drive backup (optional)

OAuth 2.0 with the ``drive.file`` scope limits access to files created or opened
by this application — not the user's entire Drive. Payloads should already be
encrypted by Student 1 before upload.

If the Google SDK is missing, credentials are absent, or the network fails, all
entry points return structured error dicts instead of raising.
"""

from __future__ import annotations

import json
from pathlib import Path

# Why: Google Drive REST client — optional; import guarded below
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    _GOOGLE_OK = True
except ImportError:
    _GOOGLE_OK = False

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
BACKUP_FOLDER_NAME = "SFFS_Backup"

# Bundled OAuth credentials — ships with the app so users need zero Google Cloud setup.
# Desktop-app client_secret is intentionally semi-public (Google's own guidance for
# installed-application OAuth; security comes from the user's Google sign-in, not this file).
_BUNDLED_SECRET = Path(__file__).parent / "google_client_secret.json"


def loadCredentials(config_dir: Path) -> "Credentials | None":
    """
    Load OAuth token from ``config_dir / google_token.json`` if present.

    Returns:
        Credentials or None if missing/invalid.
    """
    if not _GOOGLE_OK:
        return None
    token_path = Path(config_dir) / "google_token.json"
    if not token_path.exists():
        return None
    try:
        data = json.loads(token_path.read_text(encoding="utf-8"))
        return Credentials.from_authorized_user_info(data, SCOPES)
    except Exception:
        return None


def authenticateGoogleDrive(config_dir: Path, client_secrets_path: Path = None) -> "Credentials":
    """
    Run installed-app OAuth flow and persist token to ``google_token.json``.

    Args:
        config_dir: Directory where google_token.json will be saved.
        client_secrets_path: Path to client_secret.json. If None or missing,
            falls back to the bundled credentials shipped with the app — so
            end users need no Google Cloud Console access.

    Raises:
        RuntimeError: If Google libraries unavailable or flow fails.
        FileNotFoundError: If no credentials found anywhere.
    """
    if not _GOOGLE_OK:
        raise RuntimeError("Google API libraries not installed")
    # Resolve credentials: caller-supplied → bundled → error
    if client_secrets_path is None or not Path(client_secrets_path).exists():
        client_secrets_path = _BUNDLED_SECRET
    if not Path(client_secrets_path).exists():
        raise FileNotFoundError(
            "No Google OAuth credentials found. "
            "Contact the SFFS team or place client_secret.json in the config directory."
        )
    config_dir = Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_path), SCOPES)
    creds = flow.run_local_server(port=0)
    token_path = config_dir / "google_token.json"
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _assert_keystore_encrypted(local_path: Path) -> None:
    """
    Verify a keystore file has the expected encrypted structure before upload.

    WHY this check:
    Uploading a keystore JSON that lacks the KDF/ciphertext fields would mean
    uploading raw key material to Google Drive — a catastrophic secret exposure.
    This check fails fast with a clear error rather than silently uploading
    plaintext private key bytes.

    Raises:
        ValueError: If required fields are missing (file appears unencrypted).
    """
    try:
        data = json.loads(local_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Not a keystore JSON — allow upload (might be another file type)
        return
    # Only enforce for files that look like keystores (have "version" field)
    if "version" not in data:
        return
    required = {"kdf", "encrypted_private_key", "auth_tag", "iv", "salt"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(
            f"Keystore at {local_path.name} appears unencrypted — "
            f"missing fields: {sorted(missing)}. Upload aborted to prevent "
            f"raw key material exposure."
        )


def _ensure_backup_folder(service) -> str:
    """Return folder ID for SFFS_Backup, creating if needed."""
    q = f"name='{BACKUP_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    r = service.files().list(q=q, spaces="drive", fields="files(id,name)").execute()
    files = r.get("files", [])
    if files:
        return files[0]["id"]
    meta = {"name": BACKUP_FOLDER_NAME, "mimeType": "application/vnd.google-apps.folder"}
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def cloudSync(
    action: str,
    local_path: Path | None = None,
    file_id: str | None = None,
    config_dir: Path | None = None,
) -> dict:
    """
    Upload, download, list, or delete backups on Google Drive.

    Args:
        action: ``upload`` | ``download`` | ``list`` | ``delete``.
        local_path: For upload/download target path.
        file_id: Drive file id for download/delete.
        config_dir: Directory holding ``google_token.json``.

    Returns:
        Status dict (never raises for network/auth — check ``status`` key).
    """
    if not _GOOGLE_OK:
        return {"status": "offline", "message": "Google API libraries not installed"}
    if config_dir is None:
        return {"status": "not_authenticated", "message": "config_dir required"}

    creds = loadCredentials(config_dir)
    if creds is None:
        return {"status": "not_authenticated", "message": "Run authenticateGoogleDrive() first"}
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                (Path(config_dir) / "google_token.json").write_text(
                    creds.to_json(), encoding="utf-8"
                )
            except Exception as e:
                return {"status": "offline", "message": str(e)}
        else:
            return {"status": "not_authenticated", "message": "Run authenticateGoogleDrive() first"}

    try:
        service = build("drive", "v3", credentials=creds, static_discovery=False)
    except Exception as e:
        return {"status": "offline", "message": str(e)}

    try:
        if action == "upload":
            if local_path is None:
                return {"status": "error", "message": "local_path required"}
            lp = Path(local_path)
            if not lp.is_file():
                return {"status": "error", "message": "local_path must be a file"}
            # Safety check: refuse to upload keystore files that lack encryption
            # fields — prevents raw RSA private key exposure on Google Drive.
            try:
                _assert_keystore_encrypted(lp)
            except ValueError as e:
                return {"status": "error", "message": str(e)}
            parent = _ensure_backup_folder(service)
            remote_name = f"sffs_{lp.name}"
            meta = {"name": remote_name, "parents": [parent]}
            media = MediaFileUpload(str(lp), resumable=True)
            f = (
                service.files()
                .create(body=meta, media_body=media, fields="id,name")
                .execute()
            )
            return {
                "status": "uploaded",
                "file_id": f.get("id"),
                "drive_path": f"{BACKUP_FOLDER_NAME}/{remote_name}",
            }

        if action == "download":
            if file_id is None or local_path is None:
                return {"status": "error", "message": "file_id and local_path required"}
            from io import BytesIO

            from googleapiclient.http import MediaIoBaseDownload

            request = service.files().get_media(fileId=file_id)
            fh = BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            Path(local_path).write_bytes(fh.getvalue())
            return {"status": "downloaded", "local_path": Path(local_path)}

        if action == "list":
            parent = _ensure_backup_folder(service)
            r = (
                service.files()
                .list(
                    q=f"'{parent}' in parents and trashed=false",
                    fields="files(id,name,size,modifiedTime)",
                )
                .execute()
            )
            out = []
            for f in r.get("files", []):
                out.append(
                    {
                        "file_id": f["id"],
                        "name": f.get("name"),
                        "size": f.get("size"),
                        "modified": f.get("modifiedTime"),
                    }
                )
            return {"status": "ok", "files": out}

        if action == "delete":
            if file_id is None:
                return {"status": "error", "message": "file_id required"}
            service.files().delete(fileId=file_id).execute()
            return {"status": "deleted", "file_id": file_id}

        return {"status": "error", "message": f"Unknown action {action}"}
    except HttpError as e:
        return {"status": "offline", "message": str(e)}
    except OSError as e:
        return {"status": "offline", "message": str(e)}


if __name__ == "__main__":
    here = Path.cwd()
    secret = here / "client_secret.json"
    if not secret.exists():
        print("No client_secret.json in cwd — cloud sync is stubbed.")
        print(cloudSync("list", config_dir=here / "config"))
    else:
        print("client_secret.json present — run authenticateGoogleDrive from full app.")
