---
source_file: "SFFS\code2\f12_emergency_lock.py"
type: "rationale"
community: "Audit Log and Emergency Lock"
location: "L59"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Log_and_Emergency_Lock
---

# # WHY: sys.exit() is called at the end — don't trust atexit or garbage collectio

## Connections
- [[AuditLogger]] - `uses` [INFERRED]
- [[f12_emergency_lock.py]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Log_and_Emergency_Lock