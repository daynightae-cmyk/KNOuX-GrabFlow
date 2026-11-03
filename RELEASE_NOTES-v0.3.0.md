# KNOuX GrabFlow v0.3.0 — Beta release notes

Date: 2026-11-03. Status: **developer beta**, NOT published on Chrome Web Store.

## What shipped in this branch
- New dedicated **Audio** filter with direct MP3, M4A, AAC, WAV, FLAC, OGG and Opus discovery from standard HTML audio players and direct links.
- Better image discovery: `<picture>` sources, responsive `srcset`, lazy-loaded images with data placeholders, selected OpenGraph image references.
- Video remains **direct-file only**. Does not bypass DRM, capture streaming networks, download YouTube video, or promise all pages are downloadable.
- Chrome popup remains bilingual AR/EN with full RTL/LTR handling and KNOuX violet glass style.
- Default permissions unchanged: `activeTab`, `scripting`, `downloads`, `storage`; no background scanner, no telemetry and no broad host permissions.
- File naming, CSV export and 30-start batch cap retained from v0.2.
- Packaging normalizes source text line endings and includes exactly nine MV3 deployment files.

## Evidence and release gates
- Scanner/security suite: **18 passing** using Node VM mocks.
- Helpers/security suite: **7 passing** using Node.
- In-memory Chromium popup smoke: **PASS** with mocked Chrome APIs, not real extension click-grant.
- Real installed Chrome, live download completion and Chrome Web Store review: **NOT VERIFIED**.

## Follow-up after CI
Run full unpacked extension manual QA on Windows (real browser toolbar action), test controlled image/audio/video/document fixture site, actual Downloads folder and user prompts, AR/EN screenshots. Only then consider a store submission.
