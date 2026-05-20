---
source_file: "SFFS\code2\f11_write_audit_log.py"
type: "code"
community: "Audit Log and Emergency Lock"
location: "L52"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Audit_Log_and_Emergency_Lock
---

# AuditLogger

## Connections
- [[WHY Closing file handles prevents attacker from accessing decrypted files]] - `uses` [INFERRED]
- [[WHY pathlib for cross-platform path handling]] - `uses` [INFERRED]
- [[WHY signal allows catching OS signals (SIGTERM, SIGHUP) for clean shutdown on]] - `uses` [INFERRED]
- [[WHY sys and os for emergency exit and file operations]] - `uses` [INFERRED]
- [[WHY sys.exit() is called at the end — don't trust atexit or garbage collectio]] - `uses` [INFERRED]
- [[WHY threading for background threads that monitor USB and idle timeout]] - `uses` [INFERRED]
- [[.__init__()_1]] - `method` [EXTRACTED]
- [[._checkRotation()]] - `method` [EXTRACTED]
- [[._encryptFile()]] - `method` [EXTRACTED]
- [[._initialize()]] - `method` [EXTRACTED]
- [[.log()]] - `method` [EXTRACTED]
- [[.rotateLogs()]] - `method` [EXTRACTED]
- [[.verifyLogIntegrity()]] - `method` [EXTRACTED]
- [[.viewLogs()]] - `method` [EXTRACTED]
- [[Central orchestration for SFFS.]] - `uses` [INFERRED]
- [[Decrypt if needed; reuse cached sandbox file when still present.]] - `uses` [INFERRED]
- [[Decrypted files currently on disk under the session sandbox.]] - `uses` [INFERRED]
- [[Emergency lock — immediate security lockdown.      This function performs a sequ]] - `uses` [INFERRED]
- [[Reset the idle timer on user activity.      Call this on any user action (key pr]] - `uses` [INFERRED]
- [[SFFS — Student 2 interactive demo runner.  Run from code2 (imports use sibling]] - `uses` [INFERRED]
- [[SFFSCore]] - `uses` [INFERRED]
- [[Set up USB removal detection via polling.      WHY polling is used     - Kernel]] - `uses` [INFERRED]
- [[Set up idle timeout monitoring.      Args         timeout_seconds Timeout dura]] - `uses` [INFERRED]
- [[Student 2 — system security module tests.]] - `uses` [INFERRED]
- [[Thread-safe audit logger with encryption and tamper detection.      Args]] - `rationale_for` [EXTRACTED]
- [[_getLogger()]] - `calls` [EXTRACTED]
- [[f11_write_audit_log.py]] - `contains` [EXTRACTED]
- [[f12_emergency_lock.py — Student 2 System-Security Module  The threat model wha]] - `uses` [INFERRED]
- [[sffs_core.py — SFFS Application Core  Orchestrates code1 (crypto), code2 (runtim]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/Audit_Log_and_Emergency_Lock