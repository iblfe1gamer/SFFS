---
type: community
cohesion: 0.06
members: 46
---

# Audit Log and Emergency Lock

**Cohesion:** 0.06 - loosely connected
**Members:** 46 nodes

## Members
- [[WHY Closing file handles prevents attacker from accessing decrypted files]] - rationale - SFFS\code2\f12_emergency_lock.py
- [[WHY Global singleton logger instance so any module can call writeAuditLog dir]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[WHY aes module is used to encrypt the log database]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[WHY pathlib for cross-platform path handling]] - rationale - SFFS\code2\f12_emergency_lock.py
- [[WHY signal allows catching OS signals (SIGTERM, SIGHUP) for clean shutdown on]] - rationale - SFFS\code2\f12_emergency_lock.py
- [[WHY sqlite3 is built-in, lightweight, no server needed]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[WHY sys and os for emergency exit and file operations]] - rationale - SFFS\code2\f12_emergency_lock.py
- [[WHY sys.exit() is called at the end — don't trust atexit or garbage collectio]] - rationale - SFFS\code2\f12_emergency_lock.py
- [[WHY threading for background threads that monitor USB and idle timeout]] - rationale - SFFS\code2\f12_emergency_lock.py
- [[.__init__()_1]] - code - SFFS\code2\f11_write_audit_log.py
- [[._checkRotation()]] - code - SFFS\code2\f11_write_audit_log.py
- [[._encryptFile()]] - code - SFFS\code2\f11_write_audit_log.py
- [[._initialize()]] - code - SFFS\code2\f11_write_audit_log.py
- [[.log()]] - code - SFFS\code2\f11_write_audit_log.py
- [[.rotateLogs()]] - code - SFFS\code2\f11_write_audit_log.py
- [[.verifyLogIntegrity()]] - code - SFFS\code2\f11_write_audit_log.py
- [[.viewLogs()]] - code - SFFS\code2\f11_write_audit_log.py
- [[AuditLogger]] - code - SFFS\code2\f11_write_audit_log.py
- [[Check and perform log rotation if needed.]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[Emergency lock — immediate security lockdown.      This function performs a sequ]] - rationale - SFFS\code2\f12_emergency_lock.py
- [[Encrypt the entire database file if encryption key provided.]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[Get or create the global logger instance.]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[Initialize the database and create tables if not exists.]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[Reset the idle timer on user activity.      Call this on any user action (key pr]] - rationale - SFFS\code2\f12_emergency_lock.py
- [[Rotate logs by deleting oldest entries.          Args             max_entries]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[SFFS — Student 2 interactive demo runner.  Run from code2 (imports use sibling]] - rationale - SFFS\code2\run_student2.py
- [[Set up USB removal detection via polling.      WHY polling is used     - Kernel]] - rationale - SFFS\code2\f12_emergency_lock.py
- [[Set up idle timeout monitoring.      Args         timeout_seconds Timeout dura]] - rationale - SFFS\code2\f12_emergency_lock.py
- [[Thread-safe audit logger with encryption and tamper detection.      Args]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[Verify log integrity by recomputing entry hashes.          Returns]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[View recent logs.          Args             level_filter Optional log level fi]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[Write a log entry.          Args             event Event description]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[Write an audit log entry using the global singleton logger.      Args         e]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[_getLogger()]] - code - SFFS\code2\f11_write_audit_log.py
- [[_menu()_1]] - code - SFFS\code2\run_student2.py
- [[emergencyLock()]] - code - SFFS\code2\f12_emergency_lock.py
- [[emergency_callback()]] - code - SFFS\code2\f12_emergency_lock.py
- [[f11_write_audit_log.py]] - code - SFFS\code2\f11_write_audit_log.py
- [[f11_write_audit_log.py — Student 2 System-Security Module  WHY logs must be enc]] - rationale - SFFS\code2\f11_write_audit_log.py
- [[f12_emergency_lock.py]] - code - SFFS\code2\f12_emergency_lock.py
- [[f12_emergency_lock.py — Student 2 System-Security Module  The threat model wha]] - rationale - SFFS\code2\f12_emergency_lock.py
- [[resetIdleTimer()]] - code - SFFS\code2\f12_emergency_lock.py
- [[run_student2.py]] - code - SFFS\code2\run_student2.py
- [[setupIdleTimeout()]] - code - SFFS\code2\f12_emergency_lock.py
- [[setupUSBRemovalDetection()]] - code - SFFS\code2\f12_emergency_lock.py
- [[writeAuditLog()]] - code - SFFS\code2\f11_write_audit_log.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Audit_Log_and_Emergency_Lock
SORT file.name ASC
```

## Connections to other communities
- 8 edges to [[_COMMUNITY_SFFSCore Orchestrator and Monitoring]]
- 7 edges to [[_COMMUNITY_Authentication Memory and Tests]]
- 2 edges to [[_COMMUNITY_Sandbox Create and Destroy]]

## Top bridge nodes
- [[f12_emergency_lock.py]] - degree 19, connects to 3 communities
- [[run_student2.py]] - degree 8, connects to 3 communities
- [[AuditLogger]] - degree 29, connects to 2 communities
- [[f11_write_audit_log.py]] - degree 11, connects to 2 communities