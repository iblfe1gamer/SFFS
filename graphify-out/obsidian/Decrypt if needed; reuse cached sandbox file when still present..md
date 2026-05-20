---
source_file: "SFFS\main-code\sffs_core.py"
type: "rationale"
community: "SFFSCore Orchestrator and Monitoring"
location: "L248"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/SFFSCore_Orchestrator_and_Monitoring
---

# Decrypt if needed; reuse cached sandbox file when still present.

## Connections
- [[.ensure_decrypted_for_view()]] - `rationale_for` [EXTRACTED]
- [[AuditLogger]] - `uses` [INFERRED]
- [[ProcessMonitor]] - `uses` [INFERRED]
- [[SecurityError]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/SFFSCore_Orchestrator_and_Monitoring