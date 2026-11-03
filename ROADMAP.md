# KNOuX GrabFlow — evidence-based release roadmap

| Milestone | Gate | State |
| --- | --- | --- |
| Chrome MV3 core | DOM scan, bilingual popup, safe download starts | **Implemented / unit-tested** |
| v0.2 power tools | sort, large-image filter, CSS images, CSV, filename hardening | **Implemented / unit-tested / browser UI mocked** |
| CI | static checks, packaging, mocked Chromium smoke | **Committed configuration; GitHub execution pending** |
| Real Chrome integration | installed manifest, permission prompt, file completion | **Unverified** |
| Production visual QA | real extension popup screenshot, Windows, RTL, accessibility | **Unverified** |
| Store release | account, approval, privacy URL, branding/screenshots, review | **Not started** |
| VS Code companion | separate `.vsix`, Extension Host verification | **Planned** |

## Phase 1 (v0.3) — Chrome hardening
- Device test on owned machine: load unpacked, inspect inspectable popup, download own assets end-to-end.
- Handle mutable SPAs, slow pages, large asset lists, web accessibility and user-facing detailed error states.
- Explicit confirmation before bulk downloading third-party resources; cancellation/progress only if supported by Chrome APIs and storage architecture.
- Visual design review, logo source licensing and final screenshot suite.

## Phase 2 (v0.4) — intelligent discovery
- Allow user-triggered incremental rescans and smarter duplicate grouping without broad permissions.
- Refine name and extension detection, add image dimension/type reports, export JSON.
- Add optional smart selection presets; maintain no passive tracking.

## Phase 3 (v1.0) — store
- Chrome Web Store review, policy/compliance, copy, screenshots and privacy disclosures.
- Security audit and CI passing on exact target SHA, real install/download evidence.

## Phase 4 — VS Code tool
- Independent VS Code extension for references in developer-authored HTML/CSS/JS. No browser API reuse assumption.

## Product rules
Small bundle, no credential harvesting, no DRM bypass, no unapproved hidden requests, no fake PASS or download-complete claims.

### v0.4 next acceptance gates

1. Real Chrome unpacked toolbar click + activeTab grant, screenshots AR/EN RTL/LTR, direct download status including interrupted/403/404. Use a dedicated browser test profile.
2. Expand controlled video fixture matrix to MP4/WebM, HLS master quality variants, DASH, MIME-only URLs, dynamic player assets, unsupported DRM and browser-internal pages.
3. Optional Native Messaging helper for one-click HLS/DASH assembly, only with explicit user opt-in and a security audit. Desktop helper is currently manual.
4. Chrome Web Store legal/metadata/privacy review and submission — **not started**.
