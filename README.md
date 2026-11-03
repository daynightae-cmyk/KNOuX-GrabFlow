# KNOuX GrabFlow™ — Chrome MV3

**Click-to-scan page assets. Private by design. Beautifully simple.**

An independent KNOuX LABS browser extension for finding directly exposed page images, video files and downloadable documents. Bilingual English/Arabic (RTL), local-only, zero analytics, no hosted backend.

## What works in v0.2.0

- Chrome MV3, temporary `activeTab` access **only after pressing the action**. No host permissions, background listener or network interception.
- Scan page DOM for `<img>` (loaded and lazy images), `<video>` and source elements, direct document/video/image links, Open Graph *direct* video URLs, and limited inline CSS background image URLs.
- Deduplication and 600-result cap; filter by type; search; sort by page/name/type; image-size filter (known dimensions >= 800px), PNG/WEBP/etc.
- Select visible, copy selected URLs, export visible results to sanitized CSV (clipboard), start up to 30 downloads per batch into a named subfolder under Downloads.
- Windows-safe filenames and CSV formula injection protection. No writes outside user Downloads.
- Optional language preference in `chrome.storage.local`; no page data retained.

## Install for testing

1. Download or clone the repository.
2. Chrome → `chrome://extensions` → **Developer mode** → **Load unpacked** → choose the repository folder (the folder with `manifest.json`).
3. On an ordinary `http(s)` page click the KNOuX icon, review detected URLs, optionally download permitted files.

## Build a store-upload ZIP

```sh
python3 scripts/package.py
```

This emits `KNOuX-GrabFlow-CHROME-v0.2.0.zip` one directory above the source folder; it includes **only** the nine files required for Chrome, no tests, no development artifacts.

## Checks

```sh
node --check popup.js
node --check scan-page.js
node --check asset-utils.js
node tests/test-scanner.cjs
node tests/test-utilities.cjs
python tests/test-ui-inmemory.py  # requires Playwright + Chromium
```

CI runs unit/security/package tests and mocked-Chrome browser UI smoke checks. **Mocked browser UI tests are not equivalent to an installed-extension/live-download test.**

## Security/limitations

- Directly exposed `http(s)` URLs only; nothing encrypted, protected, blocked, rendered inside cross-origin frames, HLS/DASH, DRM, blob URLs, or hidden in network requests. **This is not a universal video downloader.** No YouTube video extraction.
- An offered link may expire or reject download due to server restrictions; “Downloads started” only means `chrome.downloads.download()` accepted the job, **not that a file finished successfully**.
- Asset-size filter only uses image dimensions already available to the DOM; unknown dimensions are excluded when that toggle is active.
- No auto-scanning every site, bulk crawler, credential bypass, remote telemetry, AI or server-based processing.
- Use only for content you own or are authorized to download.

## Next release gates

1. Install extension via Chrome on Windows and inspect runtime console, browser permissions and end-to-end files.
2. Inspect page screenshots and Arabic/English UX, keyboard accessibility and realistic large pages.
3. Review store data disclosure, official branding, privacy URL, screenshots and publish only after developer account authorization.
4. Separate VS Code companion extension (`.vsix`) after Chrome MVP validation.

See `ROADMAP.md`, `PRIVACY.md` and `TEST-REPORT.md`.
