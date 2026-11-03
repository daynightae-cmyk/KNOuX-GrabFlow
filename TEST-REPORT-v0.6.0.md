# KNOuX GrabFlow v0.6.0 — Full Test Report

**Date:** 2026-11-03  
**Branch:** `feature/grabflow-v0.6-ultimate-production`  
**Base:** `main` @ `367cbbf`  
**Environment:** Windows 11, Node.js v24.21.0, Python 3.14.8, Playwright 1.64.1

---

## Test Suite Summary

| Suite | File | Count | Result |
|-------|------|-------|--------|
| Scanner & Security | `tests/test-scanner.cjs` | 30/30 | ✅ PASS |
| Utility & Export | `tests/test-utilities.cjs` | 17/17 | ✅ PASS |
| VS Code Companion Contract | `tests/test-vscode-companion.cjs` | 2/2 | ✅ PASS |
| Companion Host Contract | `tests/test-companion-host.py` | 8/8 | ✅ PASS |
| FFmpeg Companion Safety | `tests/test-companion.py` | 4/4 | ✅ PASS |
| In-memory Chromium Smoke | `tests/test-ui-inmemory.py` | 1/1 | ✅ PASS |
| Browser UI Smoke | `tests/test-ui.py` | 1/1 | ✅ PASS |
| 20-Fixture Real Browser Matrix | `tests/test-e2e-matrix.py` | 20/20 | ✅ PASS |
| HLS Local Stream Integration | `tests/test-stream-integration.py` | — | ⏭ SKIP (FFmpeg not in PATH) |
| **Total Test Checks** | | **83** | **83 PASS, 0 FAIL, 1 SKIP** |

---

## Suite 1: Scanner & Security Tests (30/30)

```
PASS manifest uses MV3 with least-privilege click-to-scan and no all-sites permission
PASS extracts and normalizes image relative URLs
PASS honors currentSrc and deduplicates identical assets
PASS discovers lazy image from data-src and srcset
PASS ignores non-http data, blob, javascript and invalid links
PASS discovers direct video and files without touching network resources
PASS does not expose YouTube video links through the scanner
PASS rejects non-direct OpenGraph video URLs
PASS caps extracted asset count to 600
PASS discovers inline CSS background images without fetching them
PASS discovers directly linked images and blocks URLs with credentials
PASS falls back to real lazy URLs when currentSrc contains a data placeholder
PASS extracts responsive picture source without executing scripts or fetching resources
PASS extracts direct audio players and audio links
PASS recognizes OpenGraph images and direct media but rejects player pages
PASS rejects authenticated URLs and script-like candidate values even inside new formats
PASS records loaded image dimensions for size filtering
PASS sanitizes untrusted labels by truncating long strings
PASS detects HLS and DASH manifests but never mistakes segments for full videos
PASS finds dynamically requested direct media and HLS via resource timing names only
PASS extracts direct video contentUrl from JSON-LD VideoObject without a video tag
PASS does not expose video manifests or observed files from YouTube host
PASS discovers directly available MKV videos and classifies them as direct format
PASS extracts subtitle tracks from video element
PASS extracts video resolution and codec from MIME codecs parameter
PASS marks HLS and DASH with requires-companion eligibility and companion-assembly conversion
PASS discovers video sources from dynamic player custom elements (video-js, plyr, media-player)
PASS extracts video poster image as image asset and attaches it to video metadata
PASS extracts video duration in seconds when available
PASS discovers streaming sources from data-hls-src and data-file player attributes

30 scanner/security checks passed.
```

---

## Suite 2: Utility & Export Tests (17/17)

```
PASS sort name without mutating input
PASS large images filter keeps nonimage items
PASS filter and search compose
PASS stream filter isolates HLS/DASH streaming manifests
PASS safe file names protect Windows device names and path traversal
PASS direct audio links preserve their extension in downloads
PASS CSV quotes potentially dangerous names as text
PASS manifest imposes least privilege, no remote code or background scanner
PASS stream playlists are copy-only, direct video files are downloadable
PASS real download states are reconciled separately from download starts
PASS CSV exports media format for programmatic stream conversion
PASS safeDownloadName preserves MKV and WebM extensions accurately
PASS classifyMediaAsset constructs complete structured metadata
PASS generateFfmpegCommand constructs secure, properly quoted CLI arguments
PASS generateCurlCommand generates correct direct download command
PASS formatDuration formats seconds into clean mm:ss or hh:mm:ss strings
PASS exportAssetsJson exports structured valid JSON

17 utility/security checks passed.
```

---

## Suite 3: VS Code Companion Contract Tests (2/2)

```
PASS vscode-companion package.json exists and is valid
PASS vscode-companion extension.js exists and exports activate/deactivate

2 VS Code companion contract checks passed.
```

---

## Suite 4: Native Companion Host Contract Tests (8/8)

```
PASS test_cancel_nonexistent_job
PASS test_destination_safety_and_no_clobber
PASS test_ping_response_contract
PASS test_protocol_oversized_message_protection
PASS test_protocol_read_write
PASS test_resolve_safe_output
PASS test_ssrf_and_credential_rejections
PASS test_unknown_action

8 passed in 0.18s.
```

---

## Suite 5: 20-Fixture Real Browser Matrix E2E (20/20)

```
01_direct_mp4                  : PASS
02_direct_webm                 : PASS
03_hls_segments                : PASS
04_hls_master                  : PASS
05_dash_playlist               : PASS
06_audio_only                  : PASS
07_separate_tracks             : PASS
08_video_subtitles             : PASS
09_mime_only_url               : PASS
10_lazy_loaded                 : PASS
11_dynamic_player              : PASS
12_broken_404_handled          : PASS
13_forbidden_403_handled       : PASS
14_interrupted_transfer_handled : PASS
15_deduplication               : PASS
16_drm_protected_classified    : PASS
17_malformed_metadata_safe     : PASS
18_restricted_page_handled     : PASS
19_video_poster_extracted      : PASS
20_streams_tab_filter          : PASS

ALL 20 FIXTURE MATRIX TESTS PASSED.
```

---

## Package Verification

| Field | Value |
|-------|-------|
| Filename | `KNOuX-GrabFlow-CHROME-v0.6.0.zip` |
| Size | 87,834 bytes |
| SHA-256 | `08140E8704CB5EC45369EA23F96E48DA26EE8F08A3F87DF32E618B3A094211CA` |
| Files | 9 files (manifest, popup.html, popup.css, popup.js, scan-page.js, asset-utils.js, icons/icon16.png, icons/icon48.png, icons/icon128.png) |
