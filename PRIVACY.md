# KNOuX GrabFlow — Privacy Policy

**Version 0.5.0 · November 2026**  
**Product:** KNOuX GrabFlow Chrome Extension  
**Developer:** KNOuX LABS

---

## Summary

KNOuX GrabFlow is a local browser utility. It does not collect, transmit, or sell any personal data. All media discovery and download operations occur entirely within your browser and local machine.

---

## Permissions Used and Why

### `activeTab`
**Why:** Required to inspect the currently active page for media sources when you click the toolbar icon.  
**Scope:** Only the tab you are viewing, only when you click the icon. Never runs in the background across all tabs.

### `downloads`
**Why:** Required to initiate file downloads and monitor download progress/completion state via `chrome.downloads.search()`.  
**Scope:** Limited to downloads initiated by GrabFlow. Cannot access downloads from other sources.

### `scripting`
**Why:** Required to inject the media discovery script (`scan-page.js`) into the active page to detect video, audio, and streaming manifest sources.  
**Scope:** Injected only on demand when you click the toolbar icon. Not running continuously.

### `storage`
**Why:** Used to persist the download history list locally so it survives popup close/reopen.  
**Scope:** Stored only in `chrome.storage.local` on your device. Never synced to any external server.

### `nativeMessaging`
**Why:** Required to communicate with the optional KNOuX GrabFlow Native Media Companion (`com.knoux.grabflow.companion`) for HLS/DASH adaptive-stream assembly via FFmpeg.  
**Scope:** Messages are exchanged only with the companion host identified by `com.knoux.grabflow.companion`. The companion host is restricted to accept connections only from this extension's ID. Native messaging is only invoked when you explicitly trigger an adaptive-stream assembly.  
**Data transmitted:** Stream URL, output filename, quality selection, and progress updates only. No credentials, browsing history, or personal data are transmitted.

---

## Data Practices

| Category | Practice |
|----------|----------|
| Browsing history | Never collected or transmitted |
| Personal information | Never collected |
| Cookies / authentication tokens | Never accessed |
| Network requests (extension) | None — the extension itself makes no outbound network calls |
| Native companion network | Companion fetches only the stream URL you explicitly selected |
| Analytics / telemetry | None |
| Third-party data sharing | None |
| Data retention | Download list stored locally in `chrome.storage.local`; cleared when you click "Clear History" or uninstall the extension |

---

## DRM and Access Controls

GrabFlow does not bypass, circumvent, or decode DRM-protected content, paywalls, authentication gates, or access restrictions of any kind. If a stream is protected, GrabFlow will report "DRM-protected — not supported" and will not attempt assembly or download.

---

## FFmpeg (Native Companion Only)

When the optional Native Companion is used, FFmpeg is invoked locally on your machine to assemble adaptive streams. FFmpeg is not distributed with or embedded in this extension. You install FFmpeg separately from https://ffmpeg.org. It runs entirely under your own user account with your own file-system permissions. The companion does not communicate with any server other than the stream URL you selected.

---

## Website Data

When you click the extension toolbar icon on the currently active webpage, the extension reads that page's DOM — video/audio element sources, resource timing entries, OpenGraph metadata, JSON-LD VideoObject structured data, and page title/hostname — to identify available media. This data is used only locally within the popup to display, filter, and enable downloads. It is not sent to any remote server and is not stored between sessions (only active download job records are stored in `chrome.storage.local`).

---

## Changes from v0.4

- Added `nativeMessaging` permission (optional companion for HLS/DASH assembly)
- Extended storage use to persist download history (local only, user-clearable)
- No new data collection; no new remote endpoints

---

## Contact

For privacy questions or concerns, open an issue at:  
https://github.com/daynightae-cmyk/KNOuX-GrabFlow/issues
