# SFFS Security Model

## 1. Threat model

**Adversaries:** malware on the host, physical attacker with USB access, network eavesdroppers (for cloud backup), local debugging / inspection tools.

**Assumptions:** AES-256, RSA-2048, SHA-256, and Argon2id primitives remain secure; the OS may be hostile; decrypted files must not land on untrusted host paths (sandbox on USB).

**Out of scope:** hardware side-channels (power/EM), full memory forensics on a running machine, quantum attacks on classical crypto.

## 2. Cryptographic choices

| Algorithm | Role | Notes |
|-----------|------|--------|
| **AES-256-GCM** | File confidentiality + integrity | GCM tag + stored SHA-256 over plaintext for end-to-end check |
| **RSA-2048 OAEP** | Wrap AES file keys | Public key on disk; private key in PBKDF2-protected keystore |
| **SHA-256** | Integrity fingerprints | Compared after decrypt via `verifyHash` + `hmac.compare_digest` |
| **Argon2id** | Password hashing | Memory-hard; OWASP-style parameters in `f09` |
| **PBKDF2-SHA256** (310k iter) | Keystore encryption key | Slows brute-force on stolen `keystore_*.json` |

## 3. Security properties

- **Confidentiality:** AES + RSA wrap; keys never logged.  
- **Integrity:** GCM + hash pre/post comparison.  
- **Authentication:** Argon2id accounts; sessions in SQLite.  
- **Auditability:** Append-style audit rows with per-entry hashes (`f11`).

## 4. Attack mitigations

| Attack | Mitigation |
|--------|------------|
| Malware reading decrypted files | Sandbox under USB `sffs_data`; decrypt there |
| RAM scraping | `secureMemoryWipe` on sensitive buffers (best-effort in Python) |
| Debugger | `ProcessMonitor` + `emergencyLock` |
| Password brute force | Argon2id + lockout backoff |
| Rainbow table | Random salt per keystore / user record |
| Ciphertext tampering | GCM `InvalidTag` / `SecurityError` |
| Stolen USB | Encrypted keystore + strong master password |
| Hash / log tamper | `hmac.compare_digest`; hash-chained audit entries in logger design |
| Timing on hash compare | `hmac.compare_digest` in `verifyHash` |
| Lost USB | Optional encrypted cloud backup of key material (`cloud_sync_enabled`) |

## 5. Known limitations

- Python cannot guarantee wiping all `bytes`/`str` copies (GC, interning).  
- Windows sandbox ACLs may differ from POSIX `0700`.  
- Cloud backup needs network + OAuth maintenance.  
- Side-channel and physical attacks are not fully mitigated in software.

## 6. Security regression checklist

The following controls are pinned to automated tests in `tests/test_worker_hardening.py`:

| Control | Expected behavior | Test case |
|---------|-------------------|-----------|
| Signed IPC envelope | Valid signature accepted | `test_verify_envelope_accepts_valid_signature` |
| Anti-tamper envelope check | Forged signature rejected | `test_verify_envelope_rejects_tampered_signature` |
| Replay/staleness window | Old envelopes rejected | `test_verify_envelope_rejects_stale_request` |
| Worker output confinement | Non-sandbox output path rejected | `test_policy_guard_rejects_wrong_output_root` |
| Worker action minimization | Non-whitelisted action rejected | `test_policy_guard_rejects_disallowed_action` |
| Path traversal/escape guard | Child path outside parent rejected | `test_require_within_rejects_escape` |

## 7. OS-level isolation v1

SFFS now supports a concrete OS-enforced "v1" mode in launchers:

- **Linux:** AppArmor profile `security/apparmor/sffs-main-code.apparmor` loaded as `sffs-main-code`, launcher uses `aa-exec -p sffs-main-code`.
- **Windows:** Job Object wrapper `code2/windows_job_wrapper.py` with `KILL_ON_JOB_CLOSE` and active-process cap; `sffs.bat` routes `main.py` through that wrapper and sets `SFFS_OS_ISOLATION` / `SFFS_JOB_OBJECT_ACTIVE`. If you start `main.py` directly, `secure_app_launcher` calls `try_activate_job_for_current_process()` on first secure open so the **current** process is assigned to a job with the same limits (fails only if a parent process already holds this process in an incompatible job).
- Isolation sources are owned under `code2/` (Student 2 responsibility):
  - `code2/os_isolation.py`
  - `code2/windows_job_wrapper.py`
  - `code2/apparmor/sffs-main-code.apparmor`

Secure mode gate:

- `main-code/main.py --secure-required` calls `os_isolation.ensure_secure_mode()`.
- This gate fails closed when required confinement markers are missing.

Notes:

- Linux AppArmor is stronger confinement than app-only checks, but still requires correct host policy loading.
- Windows Job Object provides kernel-managed process constraints; full filesystem MAC is not provided by Job Objects alone.
