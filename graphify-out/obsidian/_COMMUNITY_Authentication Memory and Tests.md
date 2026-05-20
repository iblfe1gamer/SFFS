---
type: community
cohesion: 0.06
members: 35
---

# Authentication Memory and Tests

**Cohesion:** 0.06 - loosely connected
**Members:** 35 nodes

## Members
- [[WHY This is only possible because strings are implemented as memory]] - rationale - SFFS\code2\f08_secure_memory_wipe.py
- [[WHY We use bytearray for mutable overwrites]] - rationale - SFFS\code2\f08_secure_memory_wipe.py
- [[WHY bytearray allows slice assignment with zeros]] - rationale - SFFS\code2\f08_secure_memory_wipe.py
- [[WHY ctypes is the only way in Python to directly manipulate raw memory addres]] - rationale - SFFS\code2\f08_secure_memory_wipe.py
- [[Authenticate a user with password verification.      Args         username Use]] - rationale - SFFS\code2\f09_authenticate_user.py
- [[Best-effort wipe of a string via ctypes.      WARNING This is best-effort only.]] - rationale - SFFS\code2\f08_secure_memory_wipe.py
- [[Create a zeroed bytearray for secure data handling.      This function is intend]] - rationale - SFFS\code2\f08_secure_memory_wipe.py
- [[Initialize the authentication database with users and sessions tables.      Args]] - rationale - SFFS\code2\f09_authenticate_user.py
- [[Register a new user with password hashing.      Args         username Username]] - rationale - SFFS\code2\f09_authenticate_user.py
- [[Securely wipe sensitive data from memory using DOD 5220.22-M 3-pass standard.]] - rationale - SFFS\code2\f08_secure_memory_wipe.py
- [[Student 2 — system security module tests.]] - rationale - SFFS\tests\test_student2.py
- [[Terminate a session by deleting it from the database.      Args         session]] - rationale - SFFS\code2\f09_authenticate_user.py
- [[Validate a session token.      Args         session_token Session token to val]] - rationale - SFFS\code2\f09_authenticate_user.py
- [[authenticateUser()]] - code - SFFS\code2\f09_authenticate_user.py
- [[createSecureBuffer()]] - code - SFFS\code2\f08_secure_memory_wipe.py
- [[f08_secure_memory_wipe.py]] - code - SFFS\code2\f08_secure_memory_wipe.py
- [[f08_secure_memory_wipe.py — Student 2 System-Security Module  Python's del keyw]] - rationale - SFFS\code2\f08_secure_memory_wipe.py
- [[f09_authenticate_user.py]] - code - SFFS\code2\f09_authenticate_user.py
- [[f09_authenticate_user.py — Student 2 System-Security Module  Argon2id is a memo]] - rationale - SFFS\code2\f09_authenticate_user.py
- [[initAuthDatabase()]] - code - SFFS\code2\f09_authenticate_user.py
- [[registerUser()]] - code - SFFS\code2\f09_authenticate_user.py
- [[secureMemoryWipe()]] - code - SFFS\code2\f08_secure_memory_wipe.py
- [[terminateSession()]] - code - SFFS\code2\f09_authenticate_user.py
- [[test_audit_log_written_and_readable()]] - code - SFFS\tests\test_student2.py
- [[test_auth_accepts_correct_password()]] - code - SFFS\tests\test_student2.py
- [[test_auth_locks_after_max_attempts()]] - code - SFFS\tests\test_student2.py
- [[test_auth_rejects_wrong_password()]] - code - SFFS\tests\test_student2.py
- [[test_emergency_lock_wipes_sandbox()]] - code - SFFS\tests\test_student2.py
- [[test_memory_wipe_zeroes_buffer()]] - code - SFFS\tests\test_student2.py
- [[test_process_monitor_callable()]] - code - SFFS\tests\test_student2.py
- [[test_sandbox_created_and_destroyed()]] - code - SFFS\tests\test_student2.py
- [[test_sandbox_isolated_from_host()]] - code - SFFS\tests\test_student2.py
- [[test_student2.py]] - code - SFFS\tests\test_student2.py
- [[validateSession()]] - code - SFFS\code2\f09_authenticate_user.py
- [[wipeString()]] - code - SFFS\code2\f08_secure_memory_wipe.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Authentication_Memory_and_Tests
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Audit Log and Emergency Lock]]
- 3 edges to [[_COMMUNITY_SFFSCore Orchestrator and Monitoring]]
- 1 edge to [[_COMMUNITY_Sandbox Create and Destroy]]

## Top bridge nodes
- [[test_student2.py]] - degree 16, connects to 3 communities
- [[f08_secure_memory_wipe.py]] - degree 13, connects to 2 communities
- [[f09_authenticate_user.py]] - degree 11, connects to 2 communities
- [[Student 2 — system security module tests.]] - degree 2, connects to 1 community