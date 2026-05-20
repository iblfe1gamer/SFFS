---
source_file: "SFFS/docs/ARCHITECTURE.md"
type: "document"
community: "Security Model Documentation"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Security_Model_Documentation
---

# SFFS architecture: module map, init sequence, encrypt/decrypt flows, .sffs layout

## Connections
- [[.sffs binary container magic, version, IV, tag, hash_pre, size, ciphertext]] - `references` [EXTRACTED]
- [[AES-256-GCM authenticated encryption for files at rest]] - `references` [EXTRACTED]
- [[RSA-2048 OAEP wrapping of per-file AES keys (.aeswrap)]] - `references` [EXTRACTED]
- [[SFFSCore orchestrator in main-codesffs_core.py wiring students 1-3]] - `references` [EXTRACTED]
- [[SHA-256 plaintext fingerprints and verifyHash comparisons]] - `references` [EXTRACTED]
- [[USB removaldebug triggers emergencyLock, sandbox teardown, session end]] - `references` [EXTRACTED]
- [[USB-relative paths, session sandbox, decrypted_dir on removable media]] - `references` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Security_Model_Documentation