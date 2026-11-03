# KNOuX GrabFlow v0.6.1 — Native Messaging Trust Boundary

Corrective release built on v0.6.0 without recreating the extension.

## Implemented

- Refuse any browser-supplied `allowLocal` override for media probing and assembly.
- Restrict browser-requested output files to sanitized names under Downloads; block absolute paths and traversal.
- Reject wildcard Native Messaging origins and require the exact 32-character Chrome Extension ID when installing the companion.
- Generate user-specific host configuration outside the Git checkout.
- Display a missing-FFmpeg/FFprobe state rather than a misleading companion-ready indication.
- Disable the nonfunctional native assembly Cancel action rather than falsely claiming cancellation.
- Add 10 offline trust-boundary regression tests to CI.

## Not verified or incomplete

- Windows Chrome toolbar-click activeTab grant, real extension installation, and full download completion were not independently proven during this corrective slice.
- FFmpeg and FFprobe are absent from PATH on the current Windows workstation; no local HLS/DASH output verification.
- Stream redirects, nested segment SSRF and DNS rebinding need additional protections.
- Native assembly progress and reliable cancellation require persistent messaging rather than one-shot host calls.
- Not submitted to or published by the Chrome Web Store.
