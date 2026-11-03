# KNOuX GrabFlow v0.6.0 — Release Notes

**Version:** 0.6.0 (Ultimate Production Edition)  
**Date:** November 2026  
**Target:** Google Chrome Manifest V3, Windows Native Media Companion, VS Code Companion Extension

---

## Highlights

### 1. Interactive Companion Stream Assembly
- Added **⚡ Assemble** action directly onto HLS and DASH stream cards when the KNOuX Native Companion is active.
- Companion stream assembly is tracked seamlessly inside the in-popup **Download Manager** drawer with live state reconciliation (`Starting`, `Downloading`, `Complete`, `Failed`).
- If the companion is not running, a **📋 FFmpeg** command button generates a safe, ready-to-execute stream remux command with a single click.

### 2. In-Popup Media Preview Drawer
- Inline media preview modal allows users to preview direct video, audio, and images before initiating a download.
- Full respect for natural dimensions, video poster thumbnails, and sandbox boundaries.

### 3. Media Discovery Engine V2
- Recursive shadow DOM traversal discovers embedded videos in modern web components (`video-js`, `plyr`, `media-player`, `video-player`, `.jwplayer`, `.vjs-tech`).
- Same-origin `<iframe>` video discovery.
- Extraction of `<video poster="...">` assets as high-resolution images and metadata attachment.
- Video duration extraction in seconds with human-readable formatting (`mm:ss`).
- Added dedicated **Streams** filter tab to isolate HLS/DASH streaming manifests.

### 4. VS Code Media Companion Extension (`vscode-companion/`)
- Brand new companion extension for Visual Studio Code developers.
- Probes remote media streams using FFprobe, outputs stream details in a dedicated OutputChannel, and invokes KNOuX GrabFlow desktop stream assembly from the editor.
- Zero runtime dependencies.

### 5. Windows Native Companion One-Click Installers
- Added `scripts/install-companion.bat` and `scripts/uninstall-companion.bat` for effortless double-click setup.
- Expanded FFmpeg/FFprobe binary search across standard Windows directories (WinGet, Scoop, Chocolatey, LocalAppData).
- Automatic safe destination resolution inside user's `Downloads` directory.

### 6. Expanded Quality Assurance
- 30 scanner/security unit checks (+1)
- 17 utility/export checks (+5)
- 8 companion host contract checks (+1)
- 4 companion safety checks
- 2 VS Code extension contract checks (+2)
- 20-fixture Real Chromium Browser E2E Matrix (+2)
- Total automated checks: **81 test checks** across all suites.

---

## Verification Artifacts

- Package: `KNOuX-GrabFlow-CHROME-v0.6.0.zip`
- SHA-256: `08140E8704CB5EC45369EA23F96E48DA26EE8F08A3F87DF32E618B3A094211CA`
- Size: 87,834 bytes
- Manifest: Chrome Manifest V3
