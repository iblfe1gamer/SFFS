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
