---
source_file: "SFFS\code2\f12_emergency_lock.py"
type: "rationale"
community: "Audit Log and Emergency Lock"
location: "L188"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Log_and_Emergency_Lock
---

# Set up idle timeout monitoring.      Args:         timeout_seconds: Timeout dura

## Connections
- [[AuditLogger]] - `uses` [INFERRED]
- [[setupIdleTimeout()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Log_and_Emergency_Lock