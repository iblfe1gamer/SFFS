---
source_file: "SFFS\main-code\sffs_core.py"
type: "rationale"
community: "SFFSCore Orchestrator and Monitoring"
location: "L47"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/SFFSCore_Orchestrator_and_Monitoring
---

# Central orchestration for SFFS.

## Connections
- [[AuditLogger]] - `uses` [INFERRED]
- [[ProcessMonitor]] - `uses` [INFERRED]
- [[SFFSCore]] - `rationale_for` [EXTRACTED]
- [[SecurityError]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/SFFSCore_Orchestrator_and_Monitoring