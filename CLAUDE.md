# SFFS — Smart File Fortify System

## Build & run
```bash
pip install -r requirements.txt           # install deps (delegates to main-code/requirements.txt)
python main-code/main.py                  # GUI — login + dashboard
python main-code/main.py --headless       # CLI demo pipeline (no GUI)
python main-code/main.py --student 1      # student runner (1, 2, or 3)
pytest tests -q                           # run full test suite
python scripts/sffs_usb_setup.py --verify # verify USB portable install
python scripts/reset_sffs_data.py --all   # reset runtime data for clean test run
```

## Stack
- Language: Python 3.11
- GUI: PyQt6 6.6+
- Crypto: pycryptodome 3.19+, cryptography 41+
- Auth: argon2-cffi 23.1+
- Monitoring: psutil 5.9+
- Cloud: google-api-python-client (Google Drive sync)
- Platform: Windows primary; Linux CI (ubuntu-latest + xvfb for GUI tests)

## Architecture
```
code1/            # Student 1 — crypto: key gen, encrypt, decrypt, hash, secure key storage (f01–f06)
code2/            # Student 2 — security: sandbox, memory wipe, auth, process monitor, audit log, emergency lock (f07–f12)
code3/            # Student 3 — UI/cloud: drive detection, PyQt6 dashboard, file manager, cloud sync, config, threads (f13–f18)
main-code/        # Integration: main.py (entry point), sffs_core.py, isolated_worker.py
tests/            # pytest suite — per-student tests + integration + policy + hardening
docs/             # documentation
  planning/       # scaffold plans (p00–p07), project plan
apps/             # bundled portable apps (7zip, imageglass)
scripts/          # setup/verify/USB utilities
  sffs_install_deps.py   # install dependencies
  sffs_usb_setup.py      # USB setup/verify
  reset_sffs_data.py     # reset runtime data
  usb-pack/              # USB packaging scripts
sffs_data/        # RUNTIME DATA — never commit, never overwrite manually
security/         # security configs — treat as sensitive
```

## Critical rules
- Run `pytest tests -q` after editing any code file
- Never commit directly to master — branch + PR always
- Conventional commits: feat/fix/chore/docs/refactor
- Never hardcode secrets or keys — use env vars or code1/f06_secure_key_storage.py
- Each student owns their module: code1 = Student 1, code2 = Student 2, code3 = Student 3
- OS isolation markers required for `--secure-required` mode (AppArmor/Linux, Windows Job Objects/Windows)
- Block writes to: sffs_data/, security/, .env*, .pem, .key files

## CI
- `.github/workflows/tests.yml` — full pytest + USB verify + secure-mode fail-closed test
- `.github/workflows/release-gate.yml` — release gating
- GUI tests run under xvfb (continue-on-error: true)
- Windows wrapper tests run on windows-latest
