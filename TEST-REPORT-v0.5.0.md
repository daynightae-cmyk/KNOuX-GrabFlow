# KNOuX GrabFlow v0.5.0 — Test Report

**Date:** 2026-11-03  
**Branch:** `feature/grabflow-v0.5-production-engineering`  
**Implementation Commit:** `dde9cf2`  
**Base:** `main` @ `ddc6663`  
**Environment:** Windows 11, Node.js v24.21.0, Python 3.14.8, Playwright 1.64.1

---

## Test Suite Summary

| Suite | File | Count | Result |
|-------|------|-------|--------|
| Scanner & Security | `tests/test-scanner.cjs` | 29/29 | ✅ PASS |
| Utility & Export | `tests/test-utilities.cjs` | 12/12 | ✅ PASS |
| Companion Host Contract | `tests/test-companion-host.py` | 7/7 | ✅ PASS |
| E2E Browser Matrix | `tests/test-e2e-matrix.py` | 18/18 | ✅ PASS |
| HLS Stream Integration | `tests/test-stream-integration.py` | — | ⏭ SKIP |
| **Total** | | **66** | **66 PASS, 0 FAIL, SKIP** |

---

## Scanner & Security Tests (29/29)

```
PASS video/mp4 MIME type recognized as direct video
PASS video/webm MIME type recognized as direct video
PASS audio/mpeg MIME type recognized as audio
PASS application/x-mpegURL classified as streaming manifest
PASS application/dash+xml classified as streaming manifest
PASS YouTube host is excluded from scanner
PASS DRM-protected sources are flagged, not downloaded
PASS OpenGraph og:video meta detected
PASS OpenGraph og:image meta detected
PASS OpenGraph og:audio meta detected
PASS twitter:player:stream meta detected
PASS JSON-LD VideoObject contentUrl extracted
PASS HTML video src attribute detected
PASS HTML video currentSrc detected
PASS HTML source element within video detected
PASS HTML audio src attribute detected
PASS HTML anchor with download attribute detected
PASS Malformed URL does not crash scanner
PASS Oversized JSON-LD payload is skipped safely
PASS Duplicate URLs are deduplicated
PASS does not expose video manifests or observed files from YouTube host
PASS discovers directly available MKV videos and classifies them as direct format
PASS extracts subtitle tracks from video element
PASS extracts video resolution and codec from MIME codecs parameter
PASS marks HLS and DASH with requires-companion eligibility and companion-assembly conversion
PASS discovers video sources from dynamic player custom elements (video-js, plyr, media-player)
PASS HLS master manifest variant selection preserves quality options
PASS DASH MPD multi-track detection returns separate audio/video
PASS audio-only stream is classified separately from video
```

---

## Utility & Export Tests (12/12)

```
PASS safeDownloadName strips query parameters and fragments
PASS safeDownloadName handles missing extension with MIME fallback
PASS safeDownloadName preserves MKV and WebM extensions accurately
PASS classifyMediaAsset constructs complete structured metadata
PASS CSV export quotes column headers
PASS CSV export includes all expected fields
PASS CSV quotes potentially dangerous names as text
PASS manifest imposes least privilege, no remote code or background scanner
PASS stream playlists are copy-only, direct video files are downloadable
PASS real download states are reconciled separately from download starts
PASS CSV exports media format for programmatic stream conversion
PASS manifest permissions include nativeMessaging for companion
```

---

## Companion Host Contract Tests (7/7)

```
PASS protocol_read_write — length-prefixed JSON framing correct
PASS protocol_oversized_message_protection — 64MB+ message rejected
PASS ping_response_contract — {action:"ping"} → {status:"ok", version:...}
PASS ssrf_and_credential_rejections — file://, localhost, 169.254.x blocked
PASS destination_safety_and_no_clobber — existing file not overwritten
PASS cancel_nonexistent_job — returns error, does not crash
PASS unknown_action — returns {status:"error"}, does not crash
```

---

## E2E Browser Matrix (18/18)

Real Chromium browser (v156.0.8078.4) via Playwright.  
Fixtures served via local HTTP server. Chrome APIs mocked inline.  
LTR (English) and RTL (Arabic) layout verified via screenshot.

```
PASS fixture-01: direct MP4 detected and listed
PASS fixture-02: direct WebM detected and listed
PASS fixture-03: direct MKV detected and listed
PASS fixture-04: MP3 audio detected and listed
PASS fixture-05: HLS .m3u8 manifest detected, flagged requires-companion
PASS fixture-06: DASH .mpd manifest detected, flagged requires-companion
PASS fixture-07: OpenGraph og:video detected
PASS fixture-08: JSON-LD VideoObject contentUrl extracted
PASS fixture-09: twitter:player:stream meta detected
PASS fixture-10: video-js custom element scanned
PASS fixture-11: plyr custom element scanned
PASS fixture-12: media-player custom element scanned
PASS fixture-13: subtitle tracks parsed from <track> elements
PASS fixture-14: codec and resolution extracted from MIME type
PASS fixture-15: duplicate sources deduplicated
PASS fixture-16: empty page shows no assets found (no crash)
PASS fixture-17: LTR layout (English) — popup renders correctly
PASS fixture-18: RTL layout (Arabic) — popup renders correctly, text is RTL
```

**Screenshots captured:**
- `screenshots/popup-en-ltr.png` — English LTR layout
- `screenshots/popup-ar-rtl.png` — Arabic RTL layout

---

## HLS Stream Integration (SKIP)

**Status:** ⏭ SKIP — FFmpeg not present in PATH  
**Reason:** `test-stream-integration.py` correctly detects FFmpeg absence and skips.  
**Classification:** SKIP, not FAIL. Not reported as passing.  
**To verify:** Install FFmpeg, add to PATH, re-run `python -m pytest tests/test-stream-integration.py -v`

---

## Package Artifact

| Field | Value |
|-------|-------|
| Filename | `KNOuX-GrabFlow-CHROME-v0.5.0.zip` |
| Size | 24,294 bytes |
| SHA-256 | `DDB85F93DFF1F73A9D0E89A9E22F07C19924373FFC185981D00B9A30B7ED0A06` |
| Contents | manifest.json, popup.html, popup.css, popup.js, scan-page.js, asset-utils.js, icons/ |

---

## Known Limitations

| Limitation | Honest Status |
|-----------|--------------|
| End-to-end browser→companion→FFmpeg flow | NOT verified — FFmpeg absent from test environment |
| Real Chrome toolbar-click extension install | NOT automated — Chrome headless extension loading limitation |
| HLS/DASH adaptive stream assembly | NOT claimed working until live companion flow verified |
| Chrome Web Store submission | NOT submitted — requires human developer account action |
| DRM-protected streams | Correctly rejected, not bypassed |
| YouTube | Correctly excluded from scanner by design |

---

## Syntax Verification

```powershell
node --check popup.js        # exit 0
node --check scan-page.js    # exit 0
node --check asset-utils.js  # exit 0
```

All three pass `--check` (Node.js syntax-only validation).
