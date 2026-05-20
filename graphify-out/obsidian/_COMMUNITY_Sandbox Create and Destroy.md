---
type: community
cohesion: 0.12
members: 18
---

# Sandbox Create and Destroy

**Cohesion:** 0.12 - loosely connected
**Members:** 18 nodes

## Members
- [[WHY On Linux, os.chmod works with POSIX permission bits (0o700 = owner rwx on]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[WHY On Windows, we need icacls for true ACL control — stat module alone is in]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[WHY This command removes inherited permissions and grants access only to curr]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[WHY We must wipe files before deletion because standard deletion just removes]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[WHY pathlib is used for cross-platform path handling — avoids WindowsLinux s]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[WHY platform detects Windows vs Linux for different permission models]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[WHY stat is used to set restrictive file permissions programmatically]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[WHY time is needed for lock file timestamp]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[Check if a sandbox is intact and has proper security settings.      This functio]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[Create an isolated execution environment (sandbox) for secure file handling.]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[Securely destroy a sandbox by wiping its contents and removing the directory.]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[Securely wipe all files in a directory using DOD 5220.22-M 3-pass standard.]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[createIsolatedSandbox()]] - code - SFFS\code2\f07_create_isolated_sandbox.py
- [[destroySandbox()]] - code - SFFS\code2\f07_create_isolated_sandbox.py
- [[f07_create_isolated_sandbox.py]] - code - SFFS\code2\f07_create_isolated_sandbox.py
- [[f07_create_isolated_sandbox.py — Student 2 System-Security Module  An isolated]] - rationale - SFFS\code2\f07_create_isolated_sandbox.py
- [[isSandboxIntact()]] - code - SFFS\code2\f07_create_isolated_sandbox.py
- [[secureWipeDirectory()]] - code - SFFS\code2\f07_create_isolated_sandbox.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Sandbox_Create_and_Destroy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Audit Log and Emergency Lock]]
- 1 edge to [[_COMMUNITY_SFFSCore Orchestrator and Monitoring]]
- 1 edge to [[_COMMUNITY_Authentication Memory and Tests]]

## Top bridge nodes
- [[f07_create_isolated_sandbox.py]] - degree 17, connects to 3 communities