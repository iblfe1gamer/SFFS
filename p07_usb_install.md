# SFFS — Phase 7: USB Installation Guide

You are building SFFS (Smart File Fortify System). This is Phase 7: write the complete USB installation guide and the USB setup automation script.

---

## File 1: `docs/USB_INSTALLATION.md`

Write a comprehensive, step-by-step USB installation guide. This must be clear enough for a **non-technical user** to follow. Every step must include:
- What to do (exact commands or exact clicks)
- Why it's being done (one sentence)
- What success looks like
- What to do if it fails

Structure the guide as follows:

---

### Part 1: Prerequisites

**Required:**
- USB drive: minimum 2GB capacity, USB 3.0 or faster recommended
- Python 3.10 or newer

**Checking Python version:**
```bash
# Windows (in Command Prompt or PowerShell)
python --version
# or
python3 --version

# Linux (in Terminal)
python3 --version
```

If Python is not installed:
- Windows: https://www.python.org/downloads/ — check "Add Python to PATH" during install
- Linux Ubuntu/Debian: `sudo apt update && sudo apt install python3 python3-pip`
- Linux Fedora: `sudo dnf install python3 python3-pip`

---

### Part 2: Installing SFFS on the USB Drive

#### Step 1: Copy SFFS to the USB

**Windows:**
```
1. Open File Explorer
2. Open the SFFS folder on your computer
3. Select all files (Ctrl+A)
4. Copy (Ctrl+C)
5. Open your USB drive in File Explorer
6. Create a new folder called "SFFS"
7. Open that folder
8. Paste (Ctrl+V)
```

**Linux:**
```bash
# Replace /dev/sdb with your USB device (check with lsblk)
# Replace /media/user/USB with your USB mount point
cp -r /path/to/SFFS /media/user/USB/SFFS
```

Expected result: The USB should now contain an `SFFS` folder with these items:
```
USB:/SFFS/
├── sffs.bat          ← Windows launcher
├── sffs.sh           ← Linux launcher
├── main-code/
├── code1/
├── code2/
├── code3/
├── docs/
└── tests/
```

#### Step 2: Install Dependencies

**First run — Windows:**
```
1. Open the USB drive in File Explorer
2. Open the SFFS folder
3. Double-click sffs.bat
4. A black Command Prompt window will open
5. Wait for "Installing dependencies..." to complete
6. The SFFS application will start automatically
```

**First run — Linux:**
```bash
# Navigate to SFFS on the USB
cd /media/$(whoami)/*/SFFS    # adjust mount point if needed

# Make launcher executable (one-time only)
chmod +x sffs.sh

# Run SFFS
./sffs.sh
```

**Manual dependency installation (both platforms):**
```bash
pip install pycryptodome cryptography argon2-cffi psutil PyQt6 google-api-python-client google-auth-oauthlib google-auth-httplib2
```

#### Step 3: First-Time Setup

On first launch, SFFS will:
1. Detect the USB drive path automatically
2. Create an `sffs_data/` folder on the USB (this stores your keys and logs — do not delete it)
3. Ask you to create a master password

**Choosing a strong master password:**
- Minimum 12 characters
- Include: uppercase, lowercase, numbers, special characters (!@#$%^&*)
- Do NOT use: your name, birthday, common words, the same password as other accounts
- Write it down and store it somewhere safe — **if you lose it, your encrypted files cannot be recovered**

#### Step 4: Verify Installation

```bash
# Run the built-in verification
python main-code/main.py --test

# Expected output:
# ✓ Crypto module (Student 1): OK
# ✓ Security module (Student 2): OK
# ✓ UI module (Student 3): OK
# ✓ Integration: OK
# All checks passed.
```

---

### Part 3: Optional — Google Drive Cloud Backup Setup

This section is optional. SFFS works fully without cloud backup.

#### Step 1: Create a Google Cloud Project

```
1. Go to https://console.cloud.google.com/
2. Click "New Project"
3. Name it "SFFS Backup"
4. Click "Create"
```

#### Step 2: Enable Google Drive API

```
1. In the left menu, click "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click "Enable"
```

#### Step 3: Create OAuth Credentials

```
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: "Desktop application"
4. Name: "SFFS"
5. Click "Create"
6. Click "Download JSON"
7. Rename the downloaded file to "client_secret.json"
8. Copy it to: USB:/SFFS/sffs_data/config/client_secret.json
```

#### Step 4: First Cloud Sync

```
1. Open SFFS
2. Log in with your master password
3. In the dashboard, click "Cloud Sync" → "Connect to Google Drive"
4. A browser window will open — log in to your Google account
5. Click "Allow" to grant SFFS access to your Drive files
6. Return to SFFS — you should see "Google Drive: Connected"
```

---

### Part 4: Using SFFS

#### Encrypting a File

**Method 1: Drag and Drop**
```
1. Open SFFS and log in
2. Drag any file from your desktop or file manager
3. Drop it onto the SFFS window
4. Click "Encrypt"
5. Wait for the progress bar to complete
6. A .sffs file appears in the same folder as the original
7. You can now safely delete the original (SFFS does not do this automatically)
```

**Method 2: File Browser**
```
1. Open SFFS and log in
2. Click "Browse Files" in the dashboard
3. Navigate to the file you want to encrypt
4. Select the file
5. Click "Encrypt"
```

#### Decrypting a File

```
1. Open SFFS and log in
2. Drag the .sffs file onto the SFFS window (or use Browse Files)
3. Click "Decrypt"
4. Enter your master password when prompted
5. The decrypted file appears inside SFFS's secure viewer
6. You can read/edit the file INSIDE SFFS
7. When you close the file, it is wiped from memory automatically
8. To save a decrypted copy: click "Export" — it saves to your chosen location
```

---

### Part 5: Transferring SFFS to a New USB

If your USB is lost or damaged and you have cloud backup:
```
1. Copy SFFS to the new USB (repeat Part 2)
2. Open SFFS on the new USB
3. Create a new master password (it can be the same as before)
4. Click "Cloud Sync" → "Restore Keys from Backup"
5. All your previous encrypted files can now be decrypted
```

If you have NO cloud backup:
- **Your encrypted files cannot be recovered without the keys**
- This is by design — it is the same reason a lost vault key means lost access
- Always enable cloud backup for important files

---

### Part 6: Security Best Practices

```
✅ DO:
  - Store your master password somewhere safe (written down, in a secure location)
  - Enable cloud key backup for important files
  - Eject the USB properly before removing (never just yank it out)
  - Keep SFFS updated (check docs/ for update instructions)
  - Use SFFS on trusted operating systems when possible

❌ DO NOT:
  - Share your master password with anyone
  - Use SFFS on a computer you suspect is infected with a keylogger
  - Store the unencrypted original alongside the .sffs file on the same USB
  - Share your Google OAuth token (client_secret.json) with anyone
  - Use simple passwords ("password123" takes milliseconds to crack)
```

---

### Part 7: Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| `python: command not found` | Python not installed | Install Python 3.10+ from python.org |
| `ModuleNotFoundError: No module named 'Crypto'` | pycryptodome not installed | Run `pip install pycryptodome` |
| `ModuleNotFoundError: No module named 'PyQt6'` | PyQt6 not installed | Run `pip install PyQt6` |
| SFFS won't start on Linux | No display server | Run `./sffs.sh --headless` or connect a monitor |
| "File tampered or corrupted" on decrypt | File was modified after encryption | If you did not modify it, this indicates a security breach — do not trust the file |
| Forgot master password | Cannot be recovered | Without password, encrypted files are permanently inaccessible — this is the security guarantee |
| USB not detected automatically | Running from a hard drive | Pass the USB root manually: `python main.py --usb-root /media/user/MYUSB` |
| Google Drive sync fails | No internet or auth expired | Check internet connection; re-authenticate via Cloud Sync → Connect |
| `permission denied` on Linux | USB mounted without exec | Remount with exec: `sudo mount -o remount,exec /media/user/USB` |

---

## File 2: `sffs_usb_setup.py` (Automation Script)

Write a Python script that automates the full USB setup process:

```python
"""
sffs_usb_setup.py — Automated USB Setup Script

Run this script on a freshly formatted USB to set up SFFS.
It handles:
  - Detecting the USB drive
  - Copying SFFS files to USB
  - Installing Python dependencies (with --install flag)
  - Verifying the installation
  - Creating the initial sffs_data/ folder structure

Usage:
    python sffs_usb_setup.py                    # detect and show USB info
    python sffs_usb_setup.py --install          # install deps
    python sffs_usb_setup.py --verify           # verify existing install
    python sffs_usb_setup.py --copy /path/to/usb  # copy SFFS to USB
"""
```

The script should:
1. List all detected removable drives with their labels and free space
2. With `--install`: run `pip install -r requirements.txt` with a progress indicator
3. With `--verify`: check all required files exist, all imports work, print a checklist
4. With `--copy /path`: copy the SFFS directory to the specified USB path
5. Work on both Windows and Linux
6. Print clear success/failure messages with emoji status indicators (✅ ❌ ⚠️)

---

## After All Files Created

Verify:
- [ ] `docs/USB_INSTALLATION.md` has all 7 parts
- [ ] `sffs_usb_setup.py` is in the SFFS root
- [ ] `sffs_usb_setup.py --verify` runs without error

Confirm **Checkpoint 7 PASSED — Build Complete**.

---

## Final Build Verification

Run this complete verification sequence:

```bash
# 1. Verify all files exist
python sffs_usb_setup.py --verify

# 2. Run all tests
pytest tests/ -v

# 3. Run headless integration
python main-code/main.py --headless

# 4. Run each student demo
python main-code/main.py --student 1
python main-code/main.py --student 2
python main-code/main.py --student 3

# 5. Count all Python files created
find . -name "*.py" | wc -l  # Linux
dir /s /b *.py | find /c /v ""  # Windows
```

Expected output of `--verify`:
```
SFFS Installation Verification
================================
✅ code1/ — 7 files (6 functions + runner)
✅ code2/ — 7 files (6 functions + runner)
✅ code3/ — 7 files (6 functions + runner)
✅ main-code/ — 4 files (main, core, requirements, setup)
✅ docs/ — 4 documentation files
✅ tests/ — 3 test files
✅ Launchers: sffs.bat, sffs.sh
✅ All imports successful
✅ Crypto self-test: PASSED
✅ Auth self-test: PASSED
✅ USB detection: PASSED (running from: ...)

18 functions implemented across 3 modules.
SFFS is ready to use.
```
