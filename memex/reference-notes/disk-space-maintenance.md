---
last-touched: 2026-05-15
category: operations
tags: [maintenance, disk-space, windows, cleanup]
---

# Disk Space Maintenance — This Machine

Windows 10 Home, C: drive. AppData is the primary space consumer.

## Zero-Risk Cache Purges (run anytime)

```bash
pip cache purge              # ~288 MB (Python package cache, reinstalls on demand)
npm cache clean --force      # ~728 MB (Node package cache, reinstalls on demand)
```

Clear browser caches from within the browser settings (Privacy → Clear Data):
- Firefox: AppData/Local/Mozilla (~1.9 GB cache)
- Chrome: AppData/Local/Google (~1.4 GB cache)

## Already Cleaned (2026-05-15)

- Docker Desktop: uninstalled, freed Program Files/Docker
- Cursor: manually removed from AppData/Local/Programs and AppData/Local/cursor
- npm cache: purged

## Investigate Next Time Space Is Tight

| Folder | Size | Action |
|--------|------|--------|
| AppData/Local/Microsoft | 4.4 GB | Mostly Edge/Teams cache. Safe to clear caches (Settings → Privacy in Edge). Don't delete the folder. |
| AppData/Local/GitHubDesktop | 1.1 GB | Delete entirely if only using git CLI. |
| AppData/Local/Figma + Roaming/Figma | 1.5 GB combined | Clear from Figma settings. |
| AppData/Local/Adobe + Roaming/Adobe | 1.4 GB combined | Clear cache if not actively using Adobe products. |
| AppData/Local/Chromium | 545 MB | Likely from an old Electron app. Probably safe to delete entirely. |
| AppData/Roaming/Zoom | 702 MB | Old recordings and cache. Clear from Zoom settings or delete. |
| AppData/Roaming/Code | 490 MB | VS Code extensions/data. Delete if not using VS Code. |
| AppData/Roaming/VOS | 444 MB | Unknown — investigate what this is before deleting. |
| AppData/Local/pip | 288 MB | `pip cache purge` (regenerates on install). |

## How to Check Current State

```bash
# From bash — shows folders over 50 MB
powershell -ExecutionPolicy Bypass -Command "Get-ChildItem $env:LOCALAPPDATA -Directory | ForEach-Object { $s = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum; if ($s -gt 50MB) { Write-Host ([math]::Round($s/1MB,0)) 'MB' $_.Name } }"
```

## General Principles

- AppData/Local = caches and installed programs. Caches regenerate; programs need reinstalling.
- AppData/Roaming = app settings and data that syncs across machines. More permanent — check before deleting.
- `pip cache purge` and `npm cache clean --force` are always safe. Packages re-download on next install.
- Browser caches are always safe to clear from within the browser.
- When uninstalling apps on Windows, always use Settings → Apps first. Manual deletion leaves registry ghosts.
