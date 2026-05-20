---
type: community
cohesion: 0.20
members: 12
---

# RSA Keystore and Wrapping

**Cohesion:** 0.20 - loosely connected
**Members:** 12 nodes

## Members
- [[Encrypt an AES session key using RSA-OAEP for key transport.      Args]] - rationale - SFFS\code1\f06_secure_key_storage.py
- [[Generate key_id from salt and iv using SHA-256 sandwich.]] - rationale - SFFS\code1\f06_secure_key_storage.py
- [[Retrieve and decrypt an RSA private key from keystore.      Args         keysto]] - rationale - SFFS\code1\f06_secure_key_storage.py
- [[SFFS — Student 1 Secure Key Storage Module  This module provides secure storage]] - rationale - SFFS\code1\f06_secure_key_storage.py
- [[Securely store an RSA private key using PBKDF2 + AES-256-GCM.      Args]] - rationale - SFFS\code1\f06_secure_key_storage.py
- [[Unwrap an AES key that was RSA-wrapped and stored with keystore.      Args]] - rationale - SFFS\code1\f06_secure_key_storage.py
- [[f06_secure_key_storage.py]] - code - SFFS\code1\f06_secure_key_storage.py
- [[hashlib_sha256_sandwich()]] - code - SFFS\code1\f06_secure_key_storage.py
- [[retrieveKey()]] - code - SFFS\code1\f06_secure_key_storage.py
- [[secureKeyStorage()]] - code - SFFS\code1\f06_secure_key_storage.py
- [[unwrapAESKey()]] - code - SFFS\code1\f06_secure_key_storage.py
- [[wrapAESKey()]] - code - SFFS\code1\f06_secure_key_storage.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/RSA_Keystore_and_Wrapping
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Student 1 Crypto Pipeline]]
- 1 edge to [[_COMMUNITY_SFFSCore Orchestrator and Monitoring]]

## Top bridge nodes
- [[f06_secure_key_storage.py]] - degree 9, connects to 2 communities