# KNOuX GrabFlow™ — Ultimate Production Edition (v0.6.0)

**Intelligent Video & Web Asset Discovery. Private by design. Beautifully engineered.**

An independent KNOuX LABS browser extension for discovering, classifying and saving accessible video files, adaptive stream playlists, audio, images and downloadable documents. Bilingual English/Arabic (RTL), local-only, zero telemetry, no hosted backend.

---

## Current v0.6.1 capabilities and boundaries

- **Chrome MV3 Least Privilege:** Temporary `activeTab` access only upon user invocation. No broad host permissions, no remote code execution, no background activity while idle.
- **Video-First Media Engine V2:**
  - Direct video identification: MP4, WebM, MKV, MOV, M4V, OGV, WEBA.
  - Audio discovery: MP3, M4A, AAC, WAV, FLAC, OGG, OPUS.
  - Adaptive stream classification: HLS (`.m3u8`) and DASH (`.mpd`) playlists accurately labeled with variant and track information.
  - Subtitle detection: `<track kind="subtitles|captions">` inspection.
  - Codec & resolution extraction from MIME parameters and DOM dimensions.
  - Video poster extraction: high-res video thumbnails extracted and previewed.
  - Dynamic web component scanning: discovers custom elements (`video-js`, `plyr`, `media-player`, `video-player`, `.jwplayer`, `.vjs-tech`), deep shadow roots, and same-origin frames.
- **Interactive Companion Stream Assembly:**
  - One-click **⚡ Assemble** button right on HLS/DASH cards when companion is connected.
  - One-click **📋 FFmpeg** command generator when companion is not yet installed.
  - Native companion assembly is currently a one-shot request; true continuous progress and reliable cancellation are not yet verified.
- **In-Popup Media Preview Drawer:**
  - Instant playable video and audio preview with natural dimension inspection.
  - Safe sandboxed controls and CORS protection indicator.
- **Real Download Manager:**
  - Drawer integrated into the popup showing live states: `Starting`, `Downloading`, `Completed`, `Interrupted`, `Failed`.
  - Verified byte progress, file size, and error codes.
  - Chrome download actions include `Open`, `Folder`, `Retry`, `Cancel`, and `Clear History`; native assembly cancellation is disabled until a reliable persistent bridge is implemented.
- **Windows Native Media Companion:**
  - Secure Chrome Native Messaging host (`scripts/companion_host.py`) for assembling accessible HLS/DASH streams into MP4/MKV via local FFmpeg.
  - Strict security: argument-array execution (no shell interpolation), SSRF protection against private IP access, no-clobber protection (`-n`).
  - Companion installer scripts require the exact installed Chrome extension ID; wildcard registration is not permitted.
- **VS Code Media Companion Extension (`vscode-companion/`):**
  - Developer extension to inspect media URLs, validate HLS/DASH manifests, and trigger GrabFlow stream assembly from VS Code.
- **Obsidian Glass 2.0 Design System:**
  - KNOuX stag emblem with pulsing ambient violet nebula lighting.
  - Palette: `#080512` Obsidian, `#7C3AED` Violet, `#9333EA` Electric Purple, `#C084FC` Lavender Glow.
  - Full English LTR and Arabic RTL translations, keyboard navigation, and high-DPI assets.

---

## Verified release-candidate boundaries (November 2026)

- Real unpacked Chromium MV3 extension, Arabic/English RTL/LTR, real Chrome Downloads API, byte-verified PNG and playable MP4 with audio/video: locally tested.
- Actual Chrome Native Messaging host handshake and blocked unsafe browser network-policy override: locally tested with temporary HKCU registration and verified cleanup.
- HLS master and DASH assembly through the FFmpeg CLI with actual media files: locally tested with controlled fixtures.
- A physical Chrome toolbar action granting activeTab, and a complete browser-to-native stream assembly producing a finished output, remain **UNVERIFIED**.
- Chrome/Edge/Opera store submission, review and publication have **NOT** happened yet.

## Testing & Quality Gates

Run the maintained test suites (counts evolve; CI results are authoritative):

```sh
# Syntax verification
node --check popup.js
node --check scan-page.js
node --check asset-utils.js
node --check vscode-companion/extension.js

# Scanner & security unit tests (30 checks)
node tests/test-scanner.cjs

# Utility & export tests (17 checks)
node tests/test-utilities.cjs

# VS Code companion contract tests (2 checks)
node tests/test-vscode-companion.cjs

# Native companion host contract tests (8 checks)
python -m pytest tests/test-companion-host.py -v

# FFmpeg companion safety tests (4 checks)
python tests/test-companion.py

# 20-Fixture Real Browser Matrix E2E Test Suite (20 checks)
python tests/test-e2e-matrix.py
```

---

## Packaging

Build the deterministic, standard-library Chrome Web Store release package:

```sh
python scripts/package.py
```

Produces: `KNOuX-GrabFlow-CHROME-v0.6.0.zip`

---

## Known Boundaries & Honest Disclosures

- **DRM & Access Restrictions:** KNOuX GrabFlow does NOT circumvent DRM, Widevine, PlayReady, FairPlay, paywalls, or authentication gates. Protected streams are accurately classified as unsupported.
- **YouTube:** By product policy and Chrome Web Store policies, YouTube media is excluded from the scanner.
- **Native Companion Requirement:** HLS/DASH adaptive streams cannot be saved as unified movie files via Chrome Downloads API alone; they require the KNOuX Native Companion or a local FFmpeg remux command.
