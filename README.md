# KNOuX GrabFlow™ — Chrome MV3

**Intelligent Video & Web Asset Discovery. Private by design. Beautifully engineered.**

An independent KNOuX LABS browser extension for discovering, classifying and saving accessible video files, adaptive stream playlists, audio, images and downloadable documents. Bilingual English/Arabic (RTL), local-only, zero telemetry, no hosted backend.

---

## What Works in v0.5.0 Release Candidate

- **Chrome MV3 Least Privilege:** Temporary `activeTab` access only upon user invocation. No broad host permissions, no remote code execution, no background activity while idle.
- **Video-First Media Engine:**
  - Direct video identification: MP4, WebM, MKV, MOV, M4V, OGV.
  - Audio discovery: MP3, M4A, AAC, WAV, FLAC, OGG, OPUS, WEBA.
  - Adaptive stream classification: HLS (`.m3u8`) and DASH (`.mpd`) playlists accurately labeled with variant and track information.
  - Subtitle detection: `<track kind="subtitles|captions">` inspection.
  - Codec & resolution extraction from MIME parameters and DOM dimensions.
  - Bounded custom player scanning: detects dynamic web components (`video-js`, `plyr`, `media-player`, open shadow roots).
- **Real Download Manager:**
  - Drawer integrated into the popup showing live states: `Starting`, `Downloading`, `Completed`, `Interrupted`, `Failed`.
  - Verified byte progress, file size, and error codes.
  - In-app actions: `Open`, `Folder` (Explorer reveal), `Retry`, `Cancel`, `Clear History`.
- **Windows Native Media Companion:**
  - Secure Chrome Native Messaging host (`scripts/companion_host.py`) for assembling accessible HLS/DASH streams into MP4/MKV via local FFmpeg.
  - Strict security: argument-array execution (no shell interpolation), SSRF protection against private IP access, no-clobber protection (`-n`).
  - One-click registry installer: `py scripts/register_companion.py`.
- **Obsidian Glass Design System:**
  - KNOuX stag emblem with refined violet lighting.
  - Palette: `#080512` Obsidian, `#7C3AED` Violet, `#9333EA` Electric Purple, `#C084FC` Lavender Glow.
  - Full English LTR and Arabic RTL translations, keyboard navigation, and high-DPI assets.

---

## Testing & Quality Gates

Run all automated verification suites:

```sh
# Syntax verification
node --check popup.js
node --check scan-page.js
node --check asset-utils.js

# Scanner & security unit tests (29 tests)
node tests/test-scanner.cjs

# Utility & export tests (12 tests)
node tests/test-utilities.cjs

# Native companion host contract tests (7 tests)
python tests/test-companion-host.py

# FFmpeg companion safety tests (4 tests)
python tests/test-companion.py

# Popup UI integration smoke
python tests/test-ui-inmemory.py
python tests/test-ui.py

# 18-Fixture Real Browser Matrix E2E Test Suite
python tests/test-e2e-matrix.py
```

---

## Build Chrome Store Release Package

```sh
python scripts/package.py
```

Emits `KNOuX-GrabFlow-CHROME-v0.5.0.zip` (69,429 bytes, 9 runtime files, zero external dependencies).

---

## Security & Privacy Hardening

- **No Universal Permissions:** Uses click-to-scan `activeTab`.
- **Untrusted Input Defense:** Strict sanitization of URLs, filenames, and CSV export text (formula injection defense).
- **SSRF Defense:** Companion blocks local/loopback and RFC 1918 private network targets.
- **Store Prohibitions:** No DRM circumvention, YouTube downloading, or paywall bypass.
- **Privacy First:** Zero telemetry, no account requirements, zero cloud uploads.
