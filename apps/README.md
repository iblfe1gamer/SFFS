Portable Viewer Bundle (USB)
============================

Purpose
-------
This folder is reserved for portable viewer software used by SFFS when opening
decrypted sandbox files. Viewers must be launched only through the secure
launcher policy, not directly by arbitrary path.

Expected layout
---------------
Paths are defined in `apps_manifest.json` (`exe_rel` per app). Typical portable
trees match upstream zip names, for example:

- `LibreOfficePortable/App/libreoffice/program/soffice.exe` (PAF layout)
- `SumatraPDF-3.6-64/SumatraPDF-3.6-64.exe` (installer-style portable; exe name
  includes the version)
- `npp.*.portable/notepad++.exe`
- `vlc-*/vlc.exe`
- `imageglass/ImageGlass.exe` — portable zip from [ImageGlass releases](https://github.com/d2phap/ImageGlass/releases) (`ImageGlass_*_x64.zip`), or run `scripts/fetch_missing_viewers.ps1`.
- `7zip/7zFM.exe` — extract the official [7-Zip x64 `.exe`](https://www.7-zip.org/) payload with `7zr.exe` from the same release (see `scripts/fetch_missing_viewers.ps1`).

Security notes
--------------
- Only executables listed in `apps/apps_manifest.json` are trusted.
- All launched files must reside under `sffs_data/sandbox/decrypted/`.
- Process working directory should be under `sffs_data/sandbox/temp/`.
- Any temporary artifacts should be cleaned on viewer exit.
