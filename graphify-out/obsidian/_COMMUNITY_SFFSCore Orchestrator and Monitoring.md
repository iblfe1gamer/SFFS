---
type: community
cohesion: 0.07
members: 44
---

# SFFSCore Orchestrator and Monitoring

**Cohesion:** 0.07 - loosely connected
**Members:** 44 nodes

## Members
- [[WHY IsDebuggerPresent() returns non-zero if debugger attached]] - rationale - SFFS\code2\f10_monitor_process.py
- [[.__init__()]] - code - SFFS\code2\f10_monitor_process.py
- [[.__init__()_7]] - code - SFFS\main-code\sffs_core.py
- [[._ensure_rsa_keys()]] - code - SFFS\main-code\sffs_core.py
- [[._handleThreat()]] - code - SFFS\code2\f10_monitor_process.py
- [[._master_password_str()]] - code - SFFS\main-code\sffs_core.py
- [[._on_threat_detected()]] - code - SFFS\main-code\sffs_core.py
- [[._on_usb_removed()]] - code - SFFS\main-code\sffs_core.py
- [[._require_session()]] - code - SFFS\main-code\sffs_core.py
- [[.backupKeys()]] - code - SFFS\main-code\sffs_core.py
- [[.decryptFileOperation()]] - code - SFFS\main-code\sffs_core.py
- [[.encryptFileOperation()]] - code - SFFS\main-code\sffs_core.py
- [[.ensure_decrypted_for_view()]] - code - SFFS\main-code\sffs_core.py
- [[.initialize()]] - code - SFFS\main-code\sffs_core.py
- [[.list_sandbox_files()]] - code - SFFS\main-code\sffs_core.py
- [[.login()]] - code - SFFS\main-code\sffs_core.py
- [[.logout()]] - code - SFFS\main-code\sffs_core.py
- [[.run()]] - code - SFFS\code2\f10_monitor_process.py
- [[.shutdown()]] - code - SFFS\main-code\sffs_core.py
- [[.stop()]] - code - SFFS\code2\f10_monitor_process.py
- [[Background daemon thread that monitors for security threats.      Args]] - rationale - SFFS\code2\f10_monitor_process.py
- [[Central orchestration for SFFS.]] - rationale - SFFS\main-code\sffs_core.py
- [[Check for suspicious debugginganalysis tools running.      Args         None]] - rationale - SFFS\code2\f10_monitor_process.py
- [[Check if a debugger is attached to the process.      Args         None      Ret]] - rationale - SFFS\code2\f10_monitor_process.py
- [[Decrypt an SFFS file and verify integrity.      The function reads the SFFS head]] - rationale - SFFS\code1\f03_decrypt_file.py
- [[Decrypt if needed; reuse cached sandbox file when still present.]] - rationale - SFFS\main-code\sffs_core.py
- [[Decrypted files currently on disk under the session sandbox.]] - rationale - SFFS\main-code\sffs_core.py
- [[Exception]] - code
- [[Handle a detected threat.          Args             threat_type Type of threat]] - rationale - SFFS\code2\f10_monitor_process.py
- [[Main monitoring loop.          Checks for debugger attachment and suspicious pro]] - rationale - SFFS\code2\f10_monitor_process.py
- [[ProcessMonitor]] - code - SFFS\code2\f10_monitor_process.py
- [[Raised when a security violation is detected during decryption.]] - rationale - SFFS\code1\f03_decrypt_file.py
- [[SFFS — Student 1 File Decryption Module  This module decrypts SFFS (.sffs) encr]] - rationale - SFFS\code1\f03_decrypt_file.py
- [[SFFSCore]] - code - SFFS\main-code\sffs_core.py
- [[SecurityError]] - code - SFFS\code1\f03_decrypt_file.py
- [[Stop the monitoring thread cleanly.          Sets an event to terminate the loop]] - rationale - SFFS\code2\f10_monitor_process.py
- [[checkSuspiciousProcesses()]] - code - SFFS\code2\f10_monitor_process.py
- [[decryptFile()]] - code - SFFS\code1\f03_decrypt_file.py
- [[f03_decrypt_file.py]] - code - SFFS\code1\f03_decrypt_file.py
- [[f10_monitor_process.py]] - code - SFFS\code2\f10_monitor_process.py
- [[f10_monitor_process.py — Student 2 System-Security Module  Debugger attachment]] - rationale - SFFS\code2\f10_monitor_process.py
- [[isDebuggerPresent()]] - code - SFFS\code2\f10_monitor_process.py
- [[sffs_core.py]] - code - SFFS\main-code\sffs_core.py
- [[sffs_core.py — SFFS Application Core  Orchestrates code1 (crypto), code2 (runtim]] - rationale - SFFS\main-code\sffs_core.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/SFFSCore_Orchestrator_and_Monitoring
SORT file.name ASC
```

## Connections to other communities
- 8 edges to [[_COMMUNITY_Audit Log and Emergency Lock]]
- 7 edges to [[_COMMUNITY_Student 1 Crypto Pipeline]]
- 3 edges to [[_COMMUNITY_Authentication Memory and Tests]]
- 1 edge to [[_COMMUNITY_RSA Keystore and Wrapping]]
- 1 edge to [[_COMMUNITY_Sandbox Create and Destroy]]
- 1 edge to [[_COMMUNITY_USB Drive Detection]]
- 1 edge to [[_COMMUNITY_Google Drive Cloud Sync]]
- 1 edge to [[_COMMUNITY_Encrypted Config Loader]]
- 1 edge to [[_COMMUNITY_Mouse Entropy Session RNG]]

## Top bridge nodes
- [[sffs_core.py]] - degree 18, connects to 9 communities
- [[f10_monitor_process.py]] - degree 8, connects to 2 communities
- [[SFFSCore]] - degree 20, connects to 1 community
- [[SecurityError]] - degree 10, connects to 1 community
- [[f03_decrypt_file.py]] - degree 6, connects to 1 community