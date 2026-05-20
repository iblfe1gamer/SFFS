---
type: community
cohesion: 0.12
members: 32
---

# Security Model Documentation

**Cohesion:** 0.12 - loosely connected
**Members:** 32 nodes

## Members
- [[.sffs binary container magic, version, IV, tag, hash_pre, size, ciphertext]] - document - SFFS/code1/README.md
- [[AES-256-GCM authenticated encryption for files at rest]] - document - SFFS/docs/SECURITY_MODEL.md
- [[API reference for F-01 through F-18 and SFFSCore integration]] - document - SFFS/docs/API_REFERENCE.md
- [[Argon2id password hashing and SQLite-backed sessions (F-09)]] - document - SFFS/docs/SECURITY_MODEL.md
- [[Debuggersuspicious-process heuristics and ProcessMonitor daemon]] - document - SFFS/docs/API_REFERENCE.md
- [[Developer setup, structure, extension rules, pytest commands]] - document - SFFS/docs/DEVELOPER_GUIDE.md
- [[EncryptionEngine class handling AESRSA (conceptual UML)]] - paper - SFFS/GP1mk2 1.pdf
- [[FileManager class coordinating UI file operations (conceptual UML)]] - paper - SFFS/GP1mk2 1.pdf
- [[GP1mk2 slide deck SFFS background, comparison table, objectives, methodology, UML narrative]] - paper - SFFS/GP1mk2 1.pdf
- [[IsolatedEnvironment sandbox class isolating file ops (conceptual UML)]] - paper - SFFS/GP1mk2 1.pdf
- [[KeyManager class for secure key lifecycle (conceptual UML)]] - paper - SFFS/GP1mk2 1.pdf
- [[Main application README quick start, SFFSCore orchestration, security summary]] - document - SFFS/main-code/README.md
- [[Multi-factor authentication stated as futureuser-centric objective]] - paper - SFFS/GP1mk2 1.pdf
- [[Optional Google Drive OAuth upload of already-encrypted material]] - document - SFFS/code3/README.md
- [[PBKDF2-SHA256-derived key encrypting RSA private material in keystore JSON]] - document - SFFS/docs/SECURITY_MODEL.md
- [[Pinned stack pycryptodome, cryptography, argon2-cffi, psutil, PyQt6, Google APIs]] - document - SFFS/main-code/requirements.txt
- [[Plaintext fixture Hello SFFS test file]] - document - SFFS/code1/test_output/sample.txt
- [[PyQt6 dashboard, login window, worker threads for cryptofile IO]] - document - SFFS/code3/README.md
- [[RSA-2048 OAEP wrapping of per-file AES keys (.aeswrap)]] - document - SFFS/docs/ARCHITECTURE.md
- [[Root Python dependency pin (cryptography)]] - document - SFFS/requirements.txt
- [[SFFS architecture module map, init sequence, encryptdecrypt flows, .sffs layout]] - document - SFFS/docs/ARCHITECTURE.md
- [[SFFS master build plan phases, checkpoints, directory layout, dependency matrix]] - document - SFFS/plan.md
- [[SFFSCore orchestrator in main-codesffs_core.py wiring students 1-3]] - document - SFFS/docs/API_REFERENCE.md
- [[SHA-256 plaintext fingerprints and verifyHash comparisons]] - document - SFFS/docs/SECURITY_MODEL.md
- [[SQLite audit trail and writeAuditLog singleton patterns]] - document - SFFS/docs/API_REFERENCE.md
- [[Student 1 crypto module README AES-256-GCM, .sffs format, PBKDF2 demo]] - document - SFFS/code1/README.md
- [[Student 2 system security README sandbox, Argon2id, audit log, emergency lock]] - document - SFFS/code2/README.md
- [[Student 3 architect README USB paths, PyQt6 UI, Google Drive, threads]] - document - SFFS/code3/README.md
- [[Threat model, crypto choices, mitigations, known limitations]] - document - SFFS/docs/SECURITY_MODEL.md
- [[USB install guide copy tree, sffs.batsffs.sh, verify, Drive OAuth]] - document - SFFS/docs/USB_INSTALLATION.md
- [[USB removaldebug triggers emergencyLock, sandbox teardown, session end]] - document - SFFS/docs/ARCHITECTURE.md
- [[USB-relative paths, session sandbox, decrypted_dir on removable media]] - document - SFFS/docs/ARCHITECTURE.md

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Security_Model_Documentation
SORT file.name ASC
```
