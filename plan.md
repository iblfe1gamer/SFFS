# SFFS — Smart File Fortify System
## Master Build Plan

> **Project:** SFFS (Smart File Fortify System)  
> **University:** Applied Science Private University — Faculty of IT  
> **Team:** Ibraheem Snineh · Karim Taha · Mazin Alsarahin  
> **Supervisor:** Ismat Aldmour  
> **Target Platforms:** Windows 10/11 · Linux (Ubuntu 20.04+)  
> **Language:** Python 3.10+

---

## Directory Layout (Final)

```
SFFS/
├── plan.md                        ← this file
├── p00_scaffold.md                ← Claude CLI prompts (kept at repo root)
├── p01_student1.md
├── p02_student2.md
├── p03_student3.md
├── p04_main_integration.md
├── p05_runners.md
├── p06_docs.md
├── p07_usb_install.md
│
├── code1/                         ← Student 1: Crypto-Security
│   ├── __init__.py
│   ├── f01_generate_key_pairs.py
│   ├── f02_encrypt_file.py
│   ├── f03_decrypt_file.py
│   ├── f04_generate_hash.py
│   ├── f05_verify_hash.py
│   ├── f06_secure_key_storage.py
│   ├── run_student1.py            ← runs / demos all Student 1 functions
│   └── README.md
│
├── code2/                         ← Student 2: System-Security
│   ├── __init__.py
│   ├── f07_create_isolated_sandbox.py
│   ├── f08_secure_memory_wipe.py
│   ├── f09_authenticate_user.py
│   ├── f10_monitor_process.py
│   ├── f11_write_audit_log.py
│   ├── f12_emergency_lock.py
│   ├── run_student2.py
│   └── README.md
│
├── code3/                         ← Student 3: System Architect
│   ├── __init__.py
│   ├── f13_init_drive_detection.py
│   ├── f14_ui_dashboard.py
│   ├── f15_file_manager_explorer.py
│   ├── f16_cloud_sync.py
│   ├── f17_config_loader.py
│   ├── f18_thread_controller.py
│   ├── run_student3.py
│   └── README.md
│
├── main-code/                     ← Integrated full system
│   ├── __init__.py
│   ├── main.py                    ← entry point (launches full app)
│   ├── sffs_core.py               ← wires all modules together
│   ├── requirements.txt
│   ├── setup.py                   ← optional pip-installable setup
│   └── README.md
│
├── docs/                          ← Full project documentation
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── SECURITY_MODEL.md
│   ├── DEVELOPER_GUIDE.md
│   └── USB_INSTALLATION.md        ← step-by-step USB setup guide
│
└── tests/                         ← Unit tests for all modules
    ├── test_student1.py
    ├── test_student2.py
    └── test_student3.py
```

---

## Execution Order — Follow Strictly

Each phase must be **completed and verified** before starting the next.
Run prompts in the order listed. After each prompt, confirm the checkpoint passes.

```
Phase 0  →  Scaffold          (p00)   [~5 min]
Phase 1  →  Student 1 Code    (p01)   [~20 min]
Phase 2  →  Student 2 Code    (p02)   [~20 min]
Phase 3  →  Student 3 Code    (p03)   [~20 min]
Phase 4  →  Integration       (p04)   [~15 min]
Phase 5  →  Runners           (p05)   [~10 min]
Phase 6  →  Documentation     (p06)   [~15 min]
Phase 7  →  USB Install Guide (p07)   [~10 min]
```

---

## How to Run Each Prompt with Claude CLI

```bash
# Install Claude CLI first (if not already installed)
npm install -g @anthropic-ai/claude-cli
# or: pip install claude-cli

# Run a prompt file
claude < p00_scaffold.md
claude < p01_student1.md
claude < p02_student2.md
claude < p03_student3.md
claude < p04_main_integration.md
claude < p05_runners.md
claude < p06_docs.md
claude < p07_usb_install.md

# Alternative: pass as argument
claude --print p01_student1.md
```

---

## Checkpoints

### ✅ Checkpoint 0 — Scaffold
- [ ] All directories exist: `code1/`, `code2/`, `code3/`, `main-code/`, `docs/`, `tests/`
- [ ] All `__init__.py` files present
- [ ] `requirements.txt` present in `main-code/`

### ✅ Checkpoint 1 — Student 1
- [ ] 6 function files exist in `code1/`
- [ ] `python code1/run_student1.py` executes without errors
- [ ] Test: encrypt a sample file → `.sffs` created
- [ ] Test: decrypt → original file restored byte-for-byte
- [ ] Test: hash of original == hash of decrypted
- [ ] `code1/README.md` present

### ✅ Checkpoint 2 — Student 2
- [ ] 6 function files exist in `code2/`
- [ ] `python code2/run_student2.py` executes without errors
- [ ] Test: sandbox created and destroyed cleanly
- [ ] Test: `authenticateUser()` accepts correct password, rejects wrong
- [ ] Test: audit log written and readable
- [ ] `code2/README.md` present

### ✅ Checkpoint 3 — Student 3
- [ ] 6 function files exist in `code3/`
- [ ] `python code3/run_student3.py` executes without errors (UI opens)
- [ ] Test: USB root detected correctly
- [ ] Test: config save/load round-trip works
- [ ] `code3/README.md` present

### ✅ Checkpoint 4 — Integration
- [ ] `python main-code/main.py` launches full application
- [ ] Login → Dashboard flow works end-to-end
- [ ] Encrypt → Verify → Decrypt cycle works
- [ ] `main-code/README.md` present

### ✅ Checkpoint 5 — Runners
- [ ] `python code1/run_student1.py` — shows interactive demo menu
- [ ] `python code2/run_student2.py` — shows interactive demo menu
- [ ] `python code3/run_student3.py` — launches UI demo
- [ ] All runners work on both Windows and Linux

### ✅ Checkpoint 6 — Documentation
- [ ] All 5 docs files present in `docs/`
- [ ] `API_REFERENCE.md` documents all 18 functions
- [ ] `SECURITY_MODEL.md` explains cryptographic choices
- [ ] `DEVELOPER_GUIDE.md` explains how to extend each module

### ✅ Checkpoint 7 — USB Installation
- [ ] `docs/USB_INSTALLATION.md` covers Windows + Linux setup
- [ ] Autorun/launcher script for Windows (`sffs.bat`) present
- [ ] Launcher script for Linux (`sffs.sh`) present

---

## Backup Strategy

After each checkpoint, run:

```bash
# Windows
xcopy /E /I /Y . ..\SFFS_backup_checkpoint_N

# Linux
cp -r . ../SFFS_backup_checkpoint_N
```

Or use Git:
```bash
git init
git add .
git commit -m "Checkpoint N complete"
```

---

## Dependencies Summary

| Library | Purpose | Student |
|---------|---------|---------|
| `pycryptodome` | AES-256-GCM, RSA-OAEP encryption | S1 |
| `cryptography` | Key serialization, PBKDF2 | S1 |
| `argon2-cffi` | Password hashing (Argon2id) | S2 |
| `PyQt6` | GUI framework | S3 |
| `google-api-python-client` | Google Drive API | S3 |
| `google-auth-oauthlib` | OAuth 2.0 flow | S3 |
| `psutil` | Process monitoring | S2 |
| `ctypes` | Secure memory wipe | S2 |
| `pathlib` | Cross-platform paths | All |
| `sqlite3` | Audit log database | S2 |

---

## Project Objectives Coverage

| Objective | Covered By |
|-----------|-----------|
| AES-256 encryption | F-02, F-03 (S1) |
| RSA key management | F-01, F-06 (S1) |
| SHA-256 integrity | F-04, F-05 (S1) |
| Isolated execution | F-07, F-12 (S2) |
| Secure memory | F-08 (S2) |
| User authentication | F-09 (S2) |
| Anti-debugging | F-10 (S2) |
| Audit logging | F-11 (S2) |
| USB portability | F-13, F-17 (S3) |
| User-friendly UI | F-14, F-15 (S3) |
| Cloud backup | F-16 (S3) |
| Multi-threading | F-18 (S3) |
| Windows + Linux | All modules |

---

## Important Rules for All Code

1. **Every file starts with a module docstring** explaining its purpose, author, and dependencies
2. **Every function has a full docstring** with Args, Returns, Raises, and Security Notes
3. **No hardcoded paths** — all paths relative to USB root via `initDriveDetection()`
4. **No plain-text secrets** ever written to disk
5. **Cross-platform** — use `pathlib.Path` everywhere, never `os.path.join` with string slashes
6. **Every function logs its execution** to `writeAuditLog()` via the shared logger
7. **Each file is independently runnable** with an `if __name__ == "__main__":` demo block
8. **Comments explain WHY, not WHAT** — the code shows what, comments show reasoning

---

## Post-build Hardening Plan (Current)

### P1 — Secure mode and ownership
- [x] Keep OS isolation controls under `code2/` (Student 2 ownership)
- [x] Enforce secure launcher paths for Windows/Linux in release mode

### P2 — Test and CI quality
- [x] Add CI matrix for wrapper/isolation entrypoints
- [x] Replace skipped cloud-sync encryption test with deterministic mocked test

### P3 — `.aeswrap` hardening
- [x] Bind `.aeswrap` metadata to target `.sffs` identity (name + hash)
- [x] Add key commitment to wrapped-key envelope and verify on unwrap
- [x] Fail fast on wrap metadata mismatch before decrypting payload
- [x] Keep compatibility path for legacy raw wrapped-key blobs

### P4 — Audit and resilience
- [x] Introduce hash-chain linkage (`prev_hash`) in audit entries
- [x] Add replay-cache for worker IPC nonces with TTL eviction
