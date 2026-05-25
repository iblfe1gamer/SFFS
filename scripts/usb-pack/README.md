# SFFS USB Pack — Automated USB Deployment

Builds a portable SFFS (Smart File Fortify System) USB drive with a hidden partition for secure data storage.

## Quick Start

```bash
python sffs_usb_pack.py
```

This will:
1. List available USB drives and let you select one
2. Wipe and repartition the USB (visible NTFS + hidden NTFS)
3. Download Python embeddable and install dependencies
4. Copy SFFS source code to the hidden partition
5. Build PyInstaller executables (launcher + worker)
6. Copy everything to the USB
7. Verify the setup

## Options

| Flag | Description |
|------|-------------|
| `--drive E` | Use drive E: without interactive selection |
| `--list` | List available removable drives |
| `--skip-build` | Skip PyInstaller builds (use pre-built .exe files) |
| `--skip-partition` | Skip partitioning (use existing layout) |

## USB Layout

```
[Partition 1 — Visible, NTFS]
├── SFFS_launcher.exe      ← Double-click to run
├── SFFS_worker.exe        ← Decrypt subprocess
├── autorun.inf            ← Auto-launch attempt
├── README.txt             ← Linux fallback instructions
└── code1/ code2/ code3/ main-code/   ← Source for Linux

[Partition 2 — Hidden, NTFS, no drive letter]
├── .sffs_marker           ← Discovery sentinel
├── python/                ← Python embeddable + pip + deps
├── code1/ code2/ code3/ main-code/   ← Source code
└── sffs_data/             ← Keys, logs, sandbox at runtime
```

## Requirements

- Windows 10/11
- Python 3.10+ (for building)
- Administrator privileges (for diskpart partitioning)
- Internet connection (for downloading Python embeddable)
- PyInstaller (`pip install pyinstaller`)
- Pillow (`pip install Pillow`)

## Manual Build Steps

If you want to build executables separately:

```bash
# Generate icon
python generate_icon.py -o sffs.ico

# Build launcher
pyinstaller sffs_bootstrap.spec

# Build worker
pyinstaller sffs_worker.spec
```

## Linux Fallback

On Linux, all USB partitions are visible. Copy the source code directories from the visible partition to a local directory and run:

```bash
pip install -r main-code/requirements.txt
python main-code/main.py
```
