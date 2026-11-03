# KNOuX GrabFlow™ v0.5.0 Release Candidate

**Release Class:** Production Engineering & Media Pipeline Hardening  
**Target:** Google Chrome Manifest V3 + Windows Native Companion  
**Date:** November 3, 2026  

---

## 1. Executive Summary

KNOuX GrabFlow v0.5.0 transforms the extension into an exceptional, video-first, production-grade media discovery utility. It introduces a Real Download Manager, full HLS/DASH manifest classification, subtitle and track detection, Windows Native Media Companion integration over Chrome Native Messaging, and a comprehensive 18-fixture real browser E2E test suite.

---

## 2. Key Enhancements

### A. Video-First Discovery Engine
- **Direct Video Formats:** Full identification of MP4, WebM, MKV, MOV, M4V, OGV.
- **Audio Formats:** MP3, M4A, AAC, WAV, FLAC, OGG, OPUS, WEBA.
- **Track & Subtitle Detection:** Discovers `<track kind="subtitles|captions">` and exposes subtitle availability counts and languages.
- **Codec & Resolution Extraction:** Parses MIME `codecs="v,a"` parameters and natural/intrinsic dimensions.
- **Adaptive Streaming:** Differentiates direct media vs HLS (`.m3u8`) and DASH (`.mpd`) playlists. Avoids false assumptions; labels playlists truthfully.
- **Modern Dynamic Web Support:** Bounded scanning of custom web component players (`video-js`, `plyr`, `media-player`, open shadow roots).
- **Metadata Protection:** Strict URL sanitization, credential stripping, SSRF defense, 600-item resource capping.

### B. Real Download Manager
- Integrated directly into the extension popup via a dedicated management drawer.
- Shows real-time statuses proven by Chrome's Downloads API:
  - `Queued` / `Starting`
  - `Downloading` with exact byte progress (e.g. `24.5 MB / 50.0 MB (49%)`)
  - `Completed`
  - `Interrupted` / `Failed` with exact Chrome error codes
- Immediate action controls:
  - **Open File:** Opens verified completed file.
  - **Show in Folder:** Opens destination directory in Explorer.
  - **Retry:** One-click re-download for interrupted transfers.
  - **Cancel:** Terminates active downloads.
  - **Clear History:** Cleans finished records from local storage.

### C. Windows Native Media Companion
- Implements Chrome Native Messaging standard over stdio (`com.knoux.grabflow.companion`).
- **Security Guarantees:**
  - Subprocess argument array execution (strictly no shell interpolation).
  - No-clobber protection (`-n` flag in FFmpeg and destination file checks).
  - Strict URL and scheme validation (HTTP/HTTPS only).
  - SSRF protection: loopback and RFC 1918 private IP addresses blocked by default.
  - User-level registry registration via `scripts/register_companion.py` (no admin rights required).

### D. Obsidian Glass Design System
- Brand palette: Obsidian `#080512`, Violet `#7C3AED`, Electric Purple `#9333EA`, Lavender Glow `#C084FC`.
- KNOuX stag emblem with refined glow.
- Complete bilingual support: English LTR and Arabic RTL.
- Accessible keyboard navigation and WCAG AA contrast compliance.

---

## 3. Test Coverage & Verification

- **29 Scanner & Security Checks:** Unit test suite passing (`node tests/test-scanner.cjs`).
- **12 Utility & Export Checks:** CSV, safe naming, and classification tests passing (`node tests/test-utilities.cjs`).
- **7 Native Companion Host Tests:** Security, protocol, and contract tests passing (`python tests/test-companion-host.py`).
- **4 FFmpeg Safety Tests:** CLI no-clobber and argument tests passing (`python tests/test-companion.py`).
- **18-Fixture Real Browser Matrix E2E:** Full synthetic matrix passing in Chromium (`python tests/test-e2e-matrix.py`).
- **Visual Evidence:** High-DPI screenshots generated (`screenshots/popup-en-ltr.png`, `screenshots/popup-ar-rtl.png`).

---

## 4. Release Artifacts

- **Package:** `KNOuX-GrabFlow-CHROME-v0.5.0.zip`
- **SHA-256:** `D5508CD5A30B17A8C1EF0093CA50625A67CE9F4F162205153DDA07BFCF8A7FB4`
- **Runtime Size:** 69,429 bytes (9 runtime files, zero external dependencies).
