# SFFS Developer Guide

## 1. Setup

```bash
cd SFFS
pip install -r main-code/requirements.txt
pip install pytest
python main-code/main.py --test
python main-code/main.py --headless   # interactive CLI demo
```

## 2. Project structure (high level)

```
SFFS/
  code1/           # Crypto (F01-F06)
  code2/           # System security (F07-F12)
  code3/           # USB / UI / cloud / config / threads (F13-F18)
  main-code/       # sffs_core.py, main.py, requirements.txt
  tests/           # pytest
  docs/            # This documentation
  sffs.bat / sffs.sh / sffs_usb_setup.py
```

## 3. Adding a feature

1. Place crypto in `code1/`, runtime security in `code2/`, UX/portability in `code3/`.  
2. Follow existing **module docstring** + **WHY comments on imports**.  
3. Log via `AuditLogger` or `writeAuditLog` for security events.  
4. Wire high-level flows in `SFFSCore` (`main-code/sffs_core.py`).  
5. Add tests under `tests/test_studentN.py`.

## 4. Style rules (from project plan)

- `pathlib.Path` for all paths.  
- Sensitive passwords as `bytearray` when mutability/wipe matters.  
- No hardcoded drive letters — use `initDriveDetection()`.  
- Cross-platform checks where behavior differs (Windows/Linux).

## 5. Tests

```bash
pytest tests/ -v
python main-code/main.py --test
```

## 6. Common issues

| Issue | Fix |
|-------|-----|
| `No module named 'Crypto'` | `pip install pycryptodome` |
| PyQt6 on Linux headless | use `--headless` or set `DISPLAY` / Wayland |
| Google Drive | place `client_secret.json` under `sffs_data/config/` (never commit) |
| Policy errors on passwords | 12+ chars with upper, lower, digit, special (`f09`) |
