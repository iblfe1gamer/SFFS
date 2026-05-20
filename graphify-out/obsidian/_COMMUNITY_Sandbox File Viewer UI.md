---
type: community
cohesion: 0.50
members: 4
---

# Sandbox File Viewer UI

**Cohesion:** 0.50 - moderately connected
**Members:** 4 nodes

## Members
- [[Read-only viewer for files decrypted into the sandbox (text or hex preview).]] - rationale - SFFS\code3\sandbox_viewer.py
- [[Show UTF-8 text or a hex preview for binary files.]] - rationale - SFFS\code3\sandbox_viewer.py
- [[sandbox_viewer.py]] - code - SFFS\code3\sandbox_viewer.py
- [[show_sandbox_file_viewer()]] - code - SFFS\code3\sandbox_viewer.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Sandbox_File_Viewer_UI
SORT file.name ASC
```
