---
source_file: "SFFS\code1\f06_secure_key_storage.py"
type: "rationale"
community: "RSA Keystore and Wrapping"
location: "L165"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/RSA_Keystore_and_Wrapping
---

# Generate key_id from salt and iv using SHA-256 sandwich.

## Connections
- [[hashlib_sha256_sandwich()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/RSA_Keystore_and_Wrapping