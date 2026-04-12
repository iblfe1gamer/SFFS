# SFFS — Student 2: System-Security Module

This package provides sandbox isolation, secure memory wiping, Argon2id authentication, lightweight anti-debug/process checks, encrypted audit logging, and emergency lock / USB monitoring helpers.

## Prerequisites

```bash
pip install -r ../main-code/requirements.txt
```

Key dependencies: `argon2-cffi`, `psutil`, `pycryptodome` (via Student 1 stack).

## Running the demo

From the `SFFS` repository root:

```bash
python code2/run_student2.py
```

Or from `code2/`:

```bash
python run_student2.py
```

## Modules

| File | Role |
|------|------|
| `f07_create_isolated_sandbox.py` | Create/destroy isolated session sandbox |
| `f08_secure_memory_wipe.py` | Multi-pass memory wiping |
| `f09_authenticate_user.py` | SQLite auth DB, Argon2id, sessions |
| `f10_monitor_process.py` | Debugger / suspicious process heuristics |
| `f11_write_audit_log.py` | Thread-safe audit SQLite + `writeAuditLog()` |
| `f12_emergency_lock.py` | Emergency lockdown, USB / idle watchdog threads |

## Security notes

- Run demos on disposable temp directories; emergency lock calls `sys.exit()` in production paths.
- Audit logs and auth DB paths should live on the USB data tree in the full application (`initDriveDetection`).
