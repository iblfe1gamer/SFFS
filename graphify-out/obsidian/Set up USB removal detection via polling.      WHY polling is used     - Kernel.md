---
source_file: "SFFS\code2\f12_emergency_lock.py"
type: "rationale"
community: "Audit Log and Emergency Lock"
location: "L155"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Log_and_Emergency_Lock
---

# Set up USB removal detection via polling.      WHY polling is used:     - Kernel

## Connections
- [[AuditLogger]] - `uses` [INFERRED]
- [[setupUSBRemovalDetection()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Log_and_Emergency_Lock