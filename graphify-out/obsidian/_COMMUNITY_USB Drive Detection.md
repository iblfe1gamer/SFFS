---
type: community
cohesion: 0.22
members: 13
---

# USB Drive Detection

**Cohesion:** 0.22 - loosely connected
**Members:** 13 nodes

## Members
- [[Background thread invoke ``callback`` when ``usb_root`` stops existing.      Ar]] - rationale - SFFS\code3\f13_init_drive_detection.py
- [[Detect USB (or development) root and create standard SFFS directories.      Retu]] - rationale - SFFS\code3\f13_init_drive_detection.py
- [[Return (device, is_removable_guess, opts) for path's volume.]] - rationale - SFFS\code3\f13_init_drive_detection.py
- [[Return disk usage for the filesystem containing ``path``.      Args         pat]] - rationale - SFFS\code3\f13_init_drive_detection.py
- [[_linux_mount_root()]] - code - SFFS\code3\f13_init_drive_detection.py
- [[_partition_for_path()]] - code - SFFS\code3\f13_init_drive_detection.py
- [[_resolved_script_parent()]] - code - SFFS\code3\f13_init_drive_detection.py
- [[_windows_volume_root()]] - code - SFFS\code3\f13_init_drive_detection.py
- [[f13_init_drive_detection.py]] - code - SFFS\code3\f13_init_drive_detection.py
- [[f13_init_drive_detection.py — SFFS Student 3 USB  portable path layout  Portab]] - rationale - SFFS\code3\f13_init_drive_detection.py
- [[getAvailableSpace()]] - code - SFFS\code3\f13_init_drive_detection.py
- [[initDriveDetection()]] - code - SFFS\code3\f13_init_drive_detection.py
- [[monitorUSBPresence()]] - code - SFFS\code3\f13_init_drive_detection.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/USB_Drive_Detection
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_SFFSCore Orchestrator and Monitoring]]
- 1 edge to [[_COMMUNITY_Encrypted Config Loader]]

## Top bridge nodes
- [[f13_init_drive_detection.py]] - degree 10, connects to 2 communities