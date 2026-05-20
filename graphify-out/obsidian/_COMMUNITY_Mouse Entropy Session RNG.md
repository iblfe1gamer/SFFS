---
type: community
cohesion: 0.33
members: 6
---

# Mouse Entropy Session RNG

**Cohesion:** 0.33 - loosely connected
**Members:** 6 nodes

## Members
- [[Call from GUI mouse-move handler; updates an internal pool (bounded).]] - rationale - SFFS\code3\mouse_entropy.py
- [[Cryptographically strong random bytes, XOR-mixed with mouse pool if any.]] - rationale - SFFS\code3\mouse_entropy.py
- [[Mouse movement entropy — mixed with OS CSPRNG for per-session file keys.  WHY A]] - rationale - SFFS\code3\mouse_entropy.py
- [[feed_mouse_entropy()]] - code - SFFS\code3\mouse_entropy.py
- [[mouse_entropy.py]] - code - SFFS\code3\mouse_entropy.py
- [[session_random_bytes()]] - code - SFFS\code3\mouse_entropy.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Mouse_Entropy_Session_RNG
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_SFFSCore Orchestrator and Monitoring]]

## Top bridge nodes
- [[mouse_entropy.py]] - degree 4, connects to 1 community