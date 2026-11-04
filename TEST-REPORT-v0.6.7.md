# KNOuX GrabFlow v0.6.7 — P0 remediation test report

- Date: 2026-11-04
- Baseline: `main` at `1eec5ae2b660f185ce451fdd1577fc02567fc8e3` (v0.6.6)
- Release version: `0.6.7`
- Browser payload: Chrome MV3 and Edge MV3, same 12-file extension set
- Release commit: recorded in `SOURCE_SHA.txt` in the release workspace after the
  commit is created; the merged `main` SHA is verified separately in the final handoff.

## Defects corrected

### A — Inspector metadata truth (HLS/DASH)

**Before:** a 16-second HLS stream showed `Reported size: 345 B` and `Bitrate: 0 kbps`,
even though the assembled MP4 was 1,042,878 bytes.

**Cause:** `ffprobe` reports the byte size of the playlist file in `format.size`, and
reports a missing/zero `format.bit_rate` when the playlist has no measured aggregate.
The host passed those raw values through and the popup labelled the playlist bytes as
the media size and the absent bitrate as a measured zero.

**Fix:**
- `scripts/companion_host.py` now asks for `format_name`, classifies HLS/DASH as a
  playlist, and returns source-labelled metadata:
  `sizeSource: "manifest"`, `manifestBytes`, `sizeBytes: null`, `bitRate: null`,
  `bitRateSource: "unavailable"`.
- `popup.js` shows **Playlist file size**, **Media size — Unknown until assembled or
  downloaded**, and **Bitrate — Not available**. A zero-like DOM value is rejected
  rather than rendered as a measurement.
- Duration, video/audio tracks, codecs, resolution and container are preserved.

**Live Edge proof** (`tests/test-edge-native-e2e.py`, real Inspect button → native
ffprobe → FFmpeg):

```
[3b] INSPECT_METADATA_TRUTH labels=playlist/media/unknown
     details=Duration | 16.0s | Bitrate | Not available | Container | hls |
     Playlist file size | 345.0 B |
     Media size | Unknown until assembled or downloaded |
     Tracks | 320x180 h264 · aac
[5]  EDGE_PRODUCED_FILE master.mp4 1042878 bytes duration=16.04s
     tracks=['audio', 'video']
```

Screenshot: `screenshots/edge-native-inspect-v067.png`.

### B — Nested-audit wording truth

**Before:** `Nested audit: 8 references verified public`, including runs where the
controlled test deliberately allowed loopback media.

**After:** `Nested audit passed: 8 references checked`
(Arabic: `اكتمل التدقيق الداخلي: تم فحص 8 مرجعًا`).

The message now describes what the audit did — checked every nested reference against
the active policy — without claiming public address space. The actual policy is
unchanged: SSRF, DNS-rebinding pinning, redirect re-validation, private/loopback
rejection, nested key/variant/segment validation, file/script scheme rejection and the
FFmpeg transport whitelist remain enforced.

Live Edge proof:

```
[4b] AUDIT_WORDING_TRUTH text=['Nested audit passed: 8 references checked']
```

## Test inventory — 23/23 programs passed

All logs are in `evidence/` in the release workspace.

### Static, unit and security

| Program | Result |
|---|---|
| JS_SYNTAX_POPUP / SCANNER / WORKER / UTIL / VSCODE | PASS |
| SCANNER (36 checks) | PASS |
| UTILITIES (19 checks) | PASS |
| VSCODE_CONTRACT | PASS |
| PYFLAKES | PASS |
| HOST_UNIT (11 tests) | PASS |
| TRUST_BOUNDARY (10 tests) | PASS |
| COMPANION_SAFETY (8 tests) | PASS |
| METADATA_TRUTH (11 tests, new) | PASS |
| REAL_HLS_ASSEMBLY | PASS |
| HLS_DASH_MATRIX | PASS |
| NATIVE_PROTOCOL | PASS |

### Browser, UI and native runtime

| Program | Result | Evidence |
|---|---|---|
| UI_INMEMORY | PASS | New playlist-size / unknown-bitrate / EN-AR audit assertions |
| UI_HTTP_MOCK | PASS | Real Chromium popup UI, no page errors |
| BROWSER_20_FIXTURES | PASS | 20/20 fixture matrix |
| REAL_CHROMIUM_MV3 | PASS | PNG 30,752 B SHA-256 `5e2cb1db…`, MP4 68,822 B SHA-256 `401ccd2b…`, worker persistence |
| REAL_EDGE_RUNTIME | PASS | Edge 156.0.4314.58, byte-verified download, popup-close persistence, RTL/LTR |
| REAL_NATIVE_MESSAGING | PASS | Actual Chromium → registered host, browser `allowLocal` rejected, registry cleaned |
| REAL_EDGE_NATIVE_E2E | PASS | Real Inspect metadata truth, 8-reference audit wording, 11 progress samples, playable 16.04 s MP4 |

### Exact final version in live runs

- Companion handshake: `version=0.6.7`
- Edge UI badge: `FULL 0.6.7`
- Edge runtime: `EDGE_RUNTIME_PASS ... v0.6.7`

## Security regression detail

`tests/test-metadata-truth.py` adds negative assertions that remain green:

- nested loopback reference → `SSRF protection` rejection;
- nested `file:///etc/passwd` and `javascript:` references → rejected;
- public nested reference passes the audit without the result containing a
  "public address" claim;
- browser-supplied `allowLocal` remains rejected by existing trust-boundary tests;
- loopback probe/assembly remains blocked by default.

No security control was relaxed to make the wording truthful.

## Release artifacts

Built from the v0.6.7 working tree with `python scripts/package.py`, deterministic
`ZIP_STORED`, 12 whitelisted extension files, CRCs verified:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `KNOuX-GrabFlow-CHROME-v0.6.7.zip` | 167,458 | `cbdfbe26f6a30657394eae8c5f592d9f33b8af05ee3834e2d4e7616519ee9519` |
| `KNOuX-GrabFlow-EDGE-v0.6.7.zip` | 167,458 | `cbdfbe26f6a30657394eae8c5f592d9f33b8af05ee3834e2d4e7616519ee9519` |

The two browser packages carry the same payload. The ZIPs do **not** contain FFmpeg,
FFprobe or the Python companion host; HLS/DASH assembly still requires the separately
installed companion.

## Preservation

The pre-existing worktree
`D:\KNOUX-Workspace\KNOuX-GrabFlow-native-hardening-20261103` was not modified,
reset, cleaned or deleted. Its five modified/untracked files were copied with SHA-256
checksums to `preserved-native-hardening-20261103/` in the release workspace. The
worktree remains at branch `test/grabflow-real-mv3-20261103` with its original
changes intact.

The untracked `KNOuX-GrabFlow-CHROME-v0.6.2.zip` and `v0.6.2/` in the main checkout
were also left untouched.

## Honest verification boundary

**IMPLEMENTED AND VERIFIED**
- Both P0 defects fixed in source, unit/UI tests and the real Edge Inspect/assembly path.
- Chrome/Edge MV3 load-unpacked, downloads, worker persistence, RTL/LTR.
- Native messaging, real HLS/DASH assembly, progress, cancellation, FFprobe integrity.

**IMPLEMENTED BUT NOT FULLY VERIFIED**
- Chrome package on the Chrome Web Store and Edge package in Partner Center; no store
  submission or certification was performed in this task.

**UNVERIFIED / REMAINING HUMAN ACCEPTANCE**
- Physical toolbar click granting `activeTab` (headless automation cannot reproduce it).
- Actual OS clipboard acceptance in an installed browser (automation origin denied).
- External third-party CDN streams and multi-gigabyte stress.
- Firefox/Opera/Brave/Vivaldi runtime compatibility; not claimed by this release.
- VS Code Marketplace/Open VSX, Windows desktop, Android, iOS/macOS/Linux deliverables;
  these remain separate phases and are not part of the v0.6.7 browser release.

**NOT CLAIMED**
- Store approval, public publication, Firefox/Safari compatibility, mobile/desktop
  installers, or a 100% complete multiplatform family.
