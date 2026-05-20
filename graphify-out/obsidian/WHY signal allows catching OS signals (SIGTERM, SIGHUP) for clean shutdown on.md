---
source_file: "SFFS\code2\f12_emergency_lock.py"
type: "rationale"
community: "Audit Log and Emergency Lock"
location: "L49"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Log_and_Emergency_Lock
---

# # WHY: signal allows catching OS signals (SIGTERM, SIGHUP) for clean shutdown on

## Connections
- [[AuditLogger]] - `uses` [INFERRED]
- [[f12_emergency_lock.py]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Log_and_Emergency_Lock