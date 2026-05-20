---
type: community
cohesion: 0.24
members: 10
---

# Google Drive Cloud Sync

**Cohesion:** 0.24 - loosely connected
**Members:** 10 nodes

## Members
- [[Load OAuth token from ``config_dir  google_token.json`` if present.      Return]] - rationale - SFFS\code3\f16_cloud_sync.py
- [[Return folder ID for SFFS_Backup, creating if needed.]] - rationale - SFFS\code3\f16_cloud_sync.py
- [[Run installed-app OAuth flow and persist token to ``google_token.json``.      Ra]] - rationale - SFFS\code3\f16_cloud_sync.py
- [[Upload, download, list, or delete backups on Google Drive.      Args         ac]] - rationale - SFFS\code3\f16_cloud_sync.py
- [[_ensure_backup_folder()]] - code - SFFS\code3\f16_cloud_sync.py
- [[authenticateGoogleDrive()]] - code - SFFS\code3\f16_cloud_sync.py
- [[cloudSync()]] - code - SFFS\code3\f16_cloud_sync.py
- [[f16_cloud_sync.py]] - code - SFFS\code3\f16_cloud_sync.py
- [[f16_cloud_sync.py — SFFS Student 3 Google Drive backup (optional)  OAuth 2.0 wi]] - rationale - SFFS\code3\f16_cloud_sync.py
- [[loadCredentials()]] - code - SFFS\code3\f16_cloud_sync.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Google_Drive_Cloud_Sync
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_SFFSCore Orchestrator and Monitoring]]

## Top bridge nodes
- [[f16_cloud_sync.py]] - degree 6, connects to 1 community