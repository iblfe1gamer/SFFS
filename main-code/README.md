# SFFS — Main Application (`main-code/`)

## What this is

The **Smart File Fortify System (SFFS)** ties together three student modules:

- **`code1/`** — AES-256-GCM file encryption (`.sffs`), RSA-2048 keys, SHA-256 integrity  
- **`code2/`** — Sandbox, Argon2id authentication, audit logging, process monitoring, emergency lock  
- **`code3/`** — USB path layout, PyQt6 UI pieces, encrypted config, optional Google Drive sync  

`main-code/sffs_core.py` is the orchestrator; `main.py` is the entry point.

## Quick start

```bash
cd SFFS
pip install -r main-code/requirements.txt

# Full GUI (login + dashboard)
python main-code/main.py

# Non-interactive verification (register/login prompts)
python main-code/main.py --headless

# Run student demos
python main-code/main.py --student 1
python main-code/main.py --student 2
python main-code/main.py --student 3

# Run tests
python main-code/main.py --test
```

## Architecture (brief)

```
                    +-------------+
                    |  main.py    |
                    +------+------+
                           |
                    +------v------+
                    |  SFFSCore   |
                    +------+------+
           +-------------+-------------+
           |             |             |
      code1 crypto   code2 security  code3 platform
```

**Startup:** `initDriveDetection` → `configLoader` → `initAuthDatabase` → `AuditLogger` → `ProcessMonitor` → USB removal watcher.

**Encrypt (high level):** ensure RSA keys + keystore → random AES key → `encryptFile` → `wrapAESKey` → `.aeswrap` sidecar next to `.sffs`.

**Decrypt:** `unwrapAESKey` → `decryptFile` → `verifyHash`.

## Security (summary)

| Layer | Mechanism |
|-------|-----------|
| Files | AES-256-GCM (`.sffs` format) |
| Key wrap | RSA-OAEP + PEM public key |
| Private key | PBKDF2 + AES-GCM keystore (`keystore_*.json`) |
| Passwords | Argon2id (accounts) |
| Integrity | SHA-256 + GCM tag + `verifyHash` |

See `docs/SECURITY_MODEL.md` for the full model.

## Requirements

See `requirements.txt` (cryptography stack, Argon2, psutil, PyQt6, Google APIs for optional cloud).
