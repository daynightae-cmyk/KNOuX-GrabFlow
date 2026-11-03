# KNOuX GrabFlow v0.4.0 — VIDEO-FIRST beta

- Direct video detection from DOM and Resource Timing observations (never network interception).
- HLS and DASH manifests explicitly identified as playlists; never falsely offered as ready MP4 files.
- VideoObject structured metadata discovery, bounded JSON parsing, no script evaluation.
- Real browser download-state reconciliation when popup reopens (last 30 IDs only).
- Optional FFmpeg desktop companion for owner-authorized unprotected stream assembly; not bundled into Chrome Store ZIP.
- No new extension permissions; no broad host access, telemetry, or DRM circumvention.

## Verification gates

- 24 Node scanner/security checks.
- 10 utility/security checks.
- Chromium popup integration uses a **Chrome API mock**.
- Python companion safety tests and real local HLS-to-MP4 media fixture tested with FFprobe.
- Browser toolbar activeTab UX, real Chrome downloads and Chrome Web Store publication still pending.
