Portable Viewer Bundle (USB)
============================

Purpose
-------
This folder is reserved for portable viewer software used by SFFS when opening
decrypted sandbox files. Viewers must be launched only through the secure
launcher policy, not directly by arbitrary path.

Expected layout
---------------
- apps/
  - libreoffice/
    - soffice.exe
  - sumatrapdf/
    - SumatraPDF.exe
  - imageglass/
    - ImageGlass.exe
  - vlc/
    - vlc.exe
  - notepadpp/
    - notepad++.exe
  - 7zip/
    - 7zFM.exe

Security notes
--------------
- Only executables listed in `apps/apps_manifest.json` are trusted.
- All launched files must reside under `sffs_data/sandbox/decrypted/`.
- Process working directory should be under `sffs_data/sandbox/temp/`.
- Any temporary artifacts should be cleaned on viewer exit.
