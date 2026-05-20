---
source_file: "SFFS\code2\f12_emergency_lock.py"
type: "rationale"
community: "Audit Log and Emergency Lock"
location: "L234"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Log_and_Emergency_Lock
---

# Reset the idle timer on user activity.      Call this on any user action (key pr

## Connections
- [[AuditLogger]] - `uses` [INFERRED]
- [[resetIdleTimer()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Log_and_Emergency_Lock