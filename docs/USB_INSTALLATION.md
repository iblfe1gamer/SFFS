# SFFS USB Installation Guide

## Part 1 — Prerequisites

- **USB:** 2 GB+ free space (more is better).  
- **Python:** 3.10 or newer on the computer you use to prepare the stick.

**Check Python**

```text
Windows:  python --version
Linux:    python3 --version
```

Install if missing: [python.org](https://www.python.org/downloads/) (Windows: tick **Add Python to PATH**).  
Linux (Debian/Ubuntu): `sudo apt update && sudo apt install python3 python3-pip`

---

## Part 2 — Copy SFFS to the USB

1. Copy the entire `SFFS` project folder onto the USB drive (e.g. `E:\SFFS` or `/media/user/USB/SFFS`).  
2. You should see `main-code/`, `code1/`, `code2/`, `code3/`, `docs/`, `tests/`, `sffs.bat`, `sffs.sh`.

**Why:** Everything stays relative to the USB root so drive letters / mount points can change.

---

## Part 3 — First-time dependencies

**Windows:** Double-click `sffs.bat` — it installs from `main-code/requirements.txt` once and starts the app.

**Linux:**

```bash
cd /path/to/USB/SFFS
chmod +x sffs.sh
./sffs.sh
```

**Manual:** `python -m pip install -r main-code/requirements.txt`

**Success:** No `ModuleNotFoundError` when running `python main-code/main.py`.

---

## Part 4 — Verify

```bash
cd SFFS
python sffs_usb_setup.py --verify
python main-code/main.py --test
```

**Success:** Tests pass (20+), verify script prints OK lines.

---

## Part 5 — Optional Google Drive backup

1. Create a Google Cloud project → enable **Google Drive API** → **OAuth Desktop** credentials.  
2. Download JSON as `client_secret.json` into `sffs_data/config/` on the USB.  
3. Enable `cloud_sync_enabled` in config (via app or future settings UI) and run OAuth from `f16` flow.

**Why:** OAuth limits scope; files should already be encrypted before upload.

---

## Part 6 — Daily use (short)

1. Run `sffs.bat` or `./sffs.sh`.  
2. Log in (password policy applies).  
3. Encrypt: drag-and-drop or use the dashboard (master password protects the keystore / unwrap).  
4. Decrypt: pick `.sffs` and enter the same master password used for encryption.

**Why master password:** Unwraps RSA-protected AES keys from the keystore.

---

## Part 7 — Troubleshooting

| Problem | What to do |
|---------|------------|
| Python not found | Install 3.10+ and ensure PATH (Windows installer option). |
| Missing `Crypto` / `PyQt6` | Re-run `sffs.bat` / `pip install -r main-code/requirements.txt`. |
| Linux headless server | Run `python main-code/main.py --headless` or use SSH with X11/Wayland forwarding. |
| “Tampered or corrupted” | File changed after encryption — do not trust contents. |
| Forgot password | Encrypted data cannot be recovered (by design). |

---

## Security best practices

- Use strong, unique passwords; store recovery secrets offline.  
- Eject USB safely.  
- Do not commit `client_secret.json` or keystore files to public Git.
