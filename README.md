# SFFS — Smart File Fortify System

Portable **selective file encryption** for USB drives: AES-256-GCM (`.sffs`), RSA-2048 key wrapping, Argon2id accounts, sandboxed decrypt, audit logging, and an optional Google Drive backup of already-encrypted material. The same project tree runs on **Windows** and **Linux**.

---

## Features

| Area | What it does |
|------|----------------|
| **Crypto** (`code1/`) | AES-256-GCM files, RSA-OAEP wrap, SHA-256 integrity, secure keystore |
| **Runtime security** (`code2/`) | Isolated sandbox, Argon2id auth, audit DB, process heuristics, emergency lock |
| **Platform & UI** (`code3/`) | USB root detection, PyQt6 dashboard, encrypted config, optional cloud sync |
| **Core** (`main-code/`) | `SFFSCore` orchestration, `main.py` entry point |

---

## Requirements

- **Python 3.10+**
- Dependencies: see [`main-code/requirements.txt`](main-code/requirements.txt) (cryptography stack, Argon2, psutil, PyQt6, Google APIs for optional Drive)

---

## Quick start

```bash
# From the repository root (this folder)
python -m pip install -r main-code/requirements.txt
pip install pytest   # optional, for tests

# Full GUI: login + dashboard
python main-code/main.py

# Non-interactive / CI-style demo (CLI prompts)
python main-code/main.py --headless

# Student module demos
python main-code/main.py --student 1
python main-code/main.py --student 2
python main-code/main.py --student 3

# Test suite
python main-code/main.py --test
# or: pytest tests/ -v
```

**Advanced:** `python main-code/main.py --usb-root <path>` overrides the detected USB root.

---

## Launch scripts

| Script | Platform | Behavior |
|--------|----------|----------|
| [`RUN_SFFS.bat`](RUN_SFFS.bat) | Windows | Uses `.venv` if present, else `python`; runs the app (no auto `pip install`). |
| [`RUN_SFFS.sh`](RUN_SFFS.sh) | Linux / macOS | Same idea: `.venv/bin/python` or `python3` / `python`. |
| [`sffs.bat`](sffs.bat) | Windows | Optional portable Python folder, **installs deps on first run** (`.deps_installed`), then starts the app. |
| [`sffs.sh`](sffs.sh) | Linux | Installs deps on first run; uses `--headless` if no display session. |

For a **USB copy** workflow and verification commands, see [`docs/USB_INSTALLATION.md`](docs/USB_INSTALLATION.md).

---

## Project layout

```
SFFS/
├── main-code/     # main.py, sffs_core.py, requirements.txt
├── code1/         # F01–F06 crypto pipeline
├── code2/         # F07–F12 sandbox, auth, audit, monitoring
├── code3/         # F13–F18 USB, UI, config, cloud, threads
├── tests/         # pytest
├── docs/          # Architecture, security, API, USB install
├── RUN_SFFS.*     # Minimal runners
└── sffs.*         # First-run dependency install + launch
```

Runtime data (keys, encrypted config, databases) lives under **`sffs_data/`** at runtime — that directory is **not** committed (see `.gitignore`).

---

## Security model (summary)

| Layer | Mechanism |
|-------|-----------|
| Encrypted files | AES-256-GCM (`.sffs`) |
| Session key wrap | RSA-OAEP + PEM public key |
| Private key at rest | PBKDF2 + AES-GCM keystore (`keystore_*.json`) |
| Passwords | Argon2id |
| Integrity | SHA-256 + GCM tag + verification on decrypt |

Full detail: [`docs/SECURITY_MODEL.md`](docs/SECURITY_MODEL.md).

---

## Documentation

| Document | Contents |
|----------|----------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Initialization, encrypt/decrypt flows, `.sffs` layout |
| [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) | Setup, structure, style, tests, troubleshooting |
| [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) | Module API |
| [`docs/USB_INSTALLATION.md`](docs/USB_INSTALLATION.md) | Preparing a USB stick, optional Drive OAuth |
| [`main-code/README.md`](main-code/README.md) | Main app folder quick reference |

---

## Verify install

```bash
python sffs_usb_setup.py --verify
python main-code/main.py --test
```

---

## Optional: Google Drive

Place OAuth **`client_secret.json`** under `sffs_data/config/` on the machine/USB (do **not** commit it). Enable cloud sync in config per [`docs/USB_INSTALLATION.md`](docs/USB_INSTALLATION.md).

---

## Repository

**https://github.com/iblfe1gamer/SFFS**

---

## Authors

Course project — Smart File Fortify System (SFFS), integrated across `code1`, `code2`, `code3`, and `main-code`.
