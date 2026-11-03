# GrabFlow v0.6.1 — Actual Unpacked MV3 and Download Evidence

**Execution environment:** Windows, Python Playwright, Playwright Chromium with an isolated temporary browser profile; no personal Chrome profile and no mocked Chrome APIs.

## Verified locally

- The unpacked Chrome Manifest V3 extension was loaded with an actual chrome-extension:// origin.
- popup.html executed with a genuine Chrome extension runtime, including chrome.runtime, chrome.scripting and chrome.downloads.
- English LTR and Arabic RTL toggles worked without popup page errors.
- A synthetic local discovery result was supplied **inside the extension UI** for a real 1,935-byte PNG asset served from a temporary loopback fixture server.
- Clicking Download selected invoked the real Chrome Downloads API and reported download state complete.
- File bytes saved under the isolated temporary download directory matched the original PNG exactly.
- Downloaded file SHA-256: `4af76e100732d296b20229df17a84d7fd28e4c2420e8b7df5467ff5cd8ac70f8`.
- Run command: `python tests/test-real-mv3.py`; process exit code 0.

## Explicitly not proven by this test

- Physical toolbar-action click and transient activeTab permission grant.
- Unseeded dynamic discovery on a live webpage.
- Actual video download/decode or FFprobe media integrity.
- HLS/DASH native stream assembly or Native Messaging registration.
- Chrome Web Store publication.

This test uses a real installed unpacked extension and the real Downloads API, but injects a controlled fixture asset into the UI to isolate the download lifecycle. Do not reclassify this as a complete live-video E2E test.

## Integrated release QA addendum — 2026-11-03

The original report above describes the earlier PNG-only scope correctly. Following preservation on an isolated release branch, test-real-mv3.py was expanded to produce a synthetic two-second H.264/AAC MP4 on a local fixture server, download it through the actual installed Chromium MV3 extension and chrome.downloads API, compare exact file bytes and inspect the downloaded container using FFprobe.

- Actual MP4: 69,169 bytes, SHA-256 `cb1740eda76442f3ec4d109ce5b7e754c97fbc2eb639efc3428c5d028ccb1f38`; audio and video streams verified.
- Existing PNG: 1,935 bytes, SHA-256 `4af76e100732d296b20229df17a84d7fd28e4c2420e8b7df5467ff5cd8ac70f8`; exact bytes verified.
- `python tests/test-real-native-messaging-win.py`: PASS, native host ping through the actual Chromium extension runtime, FFmpeg availability verified, browser-supplied allowLocal override rejected, and the temporary HKCU registration removed and confirmed absent.
- Screenshots additionally recorded at actual 1280×800 Chrome extension resolution in both English and Arabic; the store artwork was generated from the existing stag SVG without replacing the source logo.
- `python tests/test-stream-integration.py` and `python tests/test-stream-matrix.py`: PASS on Windows, locally served HLS master and DASH with valid video/audio FFprobe outputs.
- Final local regression sweep: 17 test commands exit code 0, log at `D:\KNOUX-Workspace\_release_qa\GrabFlow-20261103\FULL_REGRESSION_RESULTS.json`.
- ZIP: `KNOuX-GrabFlow-CHROME-v0.6.1.zip`, 88,385 bytes; SHA-256 `07721c21805dd59db975fde203be36b43a494198664d32541e7a608560d40abe`; nine whitelisted extension files, CRC and exact content verified.
- Public privacy policy: https://gist.github.com/daynightae-cmyk/0af75547b262226946bc1b071f563a5f
- Still NOT VERIFIED: physical toolbar-click activeTab grant, full live browser-to-native HLS/DASH assembly, stores' certification, Firefox/Safari interoperability or production deployment.
