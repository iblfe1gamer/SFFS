---
source_file: "SFFS\code1\f03_decrypt_file.py"
type: "code"
community: "SFFSCore Orchestrator and Monitoring"
location: "L62"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/SFFSCore_Orchestrator_and_Monitoring
---

# SecurityError

## Connections
- [[Central orchestration for SFFS.]] - `uses` [INFERRED]
- [[Decrypt if needed; reuse cached sandbox file when still present.]] - `uses` [INFERRED]
- [[Decrypted files currently on disk under the session sandbox.]] - `uses` [INFERRED]
- [[Exception]] - `inherits` [EXTRACTED]
- [[Raised when a security violation is detected during decryption.]] - `rationale_for` [EXTRACTED]
- [[SFFSCore]] - `uses` [INFERRED]
- [[Student 1 — crypto module tests.]] - `uses` [INFERRED]
- [[decryptFile()]] - `calls` [EXTRACTED]
- [[f03_decrypt_file.py]] - `contains` [EXTRACTED]
- [[sffs_core.py — SFFS Application Core  Orchestrates code1 (crypto), code2 (runtim]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/SFFSCore_Orchestrator_and_Monitoring