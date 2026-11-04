# KNOuX GrabFlow™ — Full Edition (v0.6.7)

**Intelligent Video & Web Asset Discovery. Private by design. Beautifully engineered.**

An independent KNOuX LABS browser extension for Microsoft Edge and Chrome: discover, classify and
save accessible video files, adaptive stream playlists, audio, images and downloadable documents.
Bilingual English/Arabic (RTL), local-only, zero telemetry, no hosted backend.

> **Read `RELEASE_NOTES.md` and `TEST-REPORT-EDGE-FULL.md` first.** The sections
> below describe the v0.6.0–v0.6.1 baseline and several of their statements are now superseded —
> in particular "native assembly cancellation is disabled" (it works now), "one-shot request;
> continuous progress not verified" (progress streams and is tested), and the violet-only
> "Obsidian Glass 2.0" palette (the identity is now the cyan → violet neon of the orb mark).
> This is an engineering build with real Edge 156 evidence, not a store-approved release.

## What v0.6.7 fixes

| Area | Before (v0.6.6) | Now (v0.6.7) |
|---|---|---|
| HLS/DASH Inspector size | ffprobe's playlist byte size shown as "Reported size" (`345 B`) | labelled **Playlist file size**; **Media size** is explicitly unknown until assembly/download |
| Unavailable bitrate | rendered as `0 kbps` | rendered as **Not available**; a measured zero is never invented |
| Duration, tracks, codecs, resolution | correct | preserved unchanged |
| Nested audit wording | "8 references verified public" | "Nested audit passed: 8 references checked" (EN/AR) |
| Network policy | enforced | unchanged: SSRF, DNS rebinding, redirects, private addresses, nested references and FFmpeg transports remain enforced and tested |

Live Edge 156 evidence: the real Inspect button reported a 345 B playlist and a
16.0 s H.264/AAC stream, while the assembled MP4 was 1,042,878 bytes. The audit
line showed 8 references checked, not a public-address claim.

## What the v0.6.3 work added (shipped as v0.6.6)

| Area | Before | Now |
|---|---|---|
| Download lifecycle | `onChanged` lived in the popup; reporting stopped when it closed | MV3 service worker owns it; verified to survive a full popup close on Edge |
| Companion session | one-shot `sendNativeMessage`, host died with popup | persistent `connectNative` port, closed when idle |
| Assembly progress | none | real FFmpeg `-progress` frames with bytes, media time and percent |
| Assembly cancel | hard-disabled button, "needs a persistent host session" | terminates the live FFmpeg process |
| SSRF | manifest URL checked once | nested keys/variants/segments audited, redirects re-validated, DNS pinned |
| FFmpeg reach | any protocol a playlist named | `-protocol_whitelist` + `-allowed_extensions` confinement |
| Stream metadata | guessed from file names | `probe` (implemented since v0.5, never wired) shows real duration/bitrate/tracks/DRM flag |
| Edge companion | registered under the Chrome hive only — unreachable in Edge | registers Chrome **and** Edge hives |
| Edge QA | Chromium only; "could not complete Load unpacked runtime" | `tests/test-edge-runtime.py` passes 9 steps on Edge 156.0.4314.58 |
| Edge native path | companion registered under the Chrome hive only | `tests/test-edge-native-e2e.py` proves Edge → host → FFmpeg → playable file |
| Detection | DOM + resource timing at Chrome's ~250-entry default buffer | buffer raised to 3000, `initiatorType` recorded, `link rel=preload` / `object` / `embed` added |
| Identity | violet-only palette, placeholder stag icon | tokens in three layers, icons derived from the supplied orb mark |

Permissions are unchanged and still enforced by tests: `activeTab`, `scripting`, `downloads`,
`storage`, `nativeMessaging`. No host permissions, no `webRequest`, no `declarativeNetRequest`.
The manifest test was rewritten rather than removed: it now asserts the worker contains no
traffic-observation code, which is the guarantee the old `background === undefined` assertion was
standing in for.


---

## Current v0.6.1 capabilities and boundaries

- **Chrome MV3 Least Privilege:** Temporary `activeTab` access only upon user invocation. No broad host permissions, no remote code execution, no background activity while idle.
- **Video-First Media Engine V2:**
  - Direct video identification: MP4, WebM, MKV, MOV, M4V, OGV, WEBA.
  - Audio discovery: MP3, M4A, AAC, WAV, FLAC, OGG, OPUS.
  - Adaptive stream classification: HLS (`.m3u8`) and DASH (`.mpd`) playlists accurately labeled with variant and track information.
  - Subtitle detection: `<track kind="subtitles|captions">` inspection.
  - Codec & resolution extraction from MIME parameters and DOM dimensions.
  - Video poster extraction: high-res video thumbnails extracted and previewed.
  - Dynamic web component scanning: discovers custom elements (`video-js`, `plyr`, `media-player`, `video-player`, `.jwplayer`, `.vjs-tech`), deep shadow roots, and same-origin frames.
- **Interactive Companion Stream Assembly:**
  - One-click **⚡ Assemble** button right on HLS/DASH cards when companion is connected.
  - One-click **📋 FFmpeg** command generator when companion is not yet installed.
  - Native companion assembly is currently a one-shot request; true continuous progress and reliable cancellation are not yet verified.
- **In-Popup Media Preview Drawer:**
  - Instant playable video and audio preview with natural dimension inspection.
  - Safe sandboxed controls and CORS protection indicator.
- **Real Download Manager:**
  - Drawer integrated into the popup showing live states: `Starting`, `Downloading`, `Completed`, `Interrupted`, `Failed`.
  - Verified byte progress, file size, and error codes.
  - Chrome download actions include `Open`, `Folder`, `Retry`, `Cancel`, and `Clear History`; native assembly cancellation is disabled until a reliable persistent bridge is implemented.
- **Windows Native Media Companion:**
  - Secure Chrome Native Messaging host (`scripts/companion_host.py`) for assembling accessible HLS/DASH streams into MP4/MKV via local FFmpeg.
  - Strict security: argument-array execution (no shell interpolation), SSRF protection against private IP access, no-clobber protection (`-n`).
  - Companion installer scripts require the exact installed Chrome extension ID; wildcard registration is not permitted.
- **VS Code Media Companion Extension (`vscode-companion/`):**
  - Developer extension to inspect media URLs, validate HLS/DASH manifests, and trigger GrabFlow stream assembly from VS Code.
- **GrabFlow Neon Design System:**
  - Orb mark derived from the supplied logo by `scripts/build-icons.py`; pulsing cyan/violet ambient lighting.
  - Three token layers — primitive, semantic, component — with the signature gradient
    `#22D3EE → #8B5CF6 → #E879F9` on a deep indigo field. Rules reference tokens, never raw hex.
  - Full English LTR and Arabic RTL translations, keyboard navigation, and high-DPI assets.

---

## Verified release-candidate boundaries (November 2026)

- Real unpacked Chromium MV3 extension, Arabic/English RTL/LTR, real Chrome Downloads API, byte-verified PNG and playable MP4 with audio/video: locally tested.
- Actual Chrome Native Messaging host handshake and blocked unsafe browser network-policy override: locally tested with temporary HKCU registration and verified cleanup.
- HLS master and DASH assembly through the FFmpeg CLI with actual media files: locally tested with controlled fixtures.
- A physical Chrome toolbar action granting activeTab, and a complete browser-to-native stream assembly producing a finished output, remain **UNVERIFIED**.
- Chrome/Edge/Opera store submission, review and publication have **NOT** happened yet.

## Testing & Quality Gates

Run the maintained test suites (counts evolve; CI results are authoritative):

```sh
# Syntax verification
node --check popup.js
node --check scan-page.js
node --check asset-utils.js
node --check vscode-companion/extension.js

# Scanner & security unit tests (36 checks)
node tests/test-scanner.cjs

# Utility, export and CSS-contract tests (18 checks)
node tests/test-utilities.cjs

# VS Code companion contract tests (2 checks)
node tests/test-vscode-companion.cjs

# Native companion host contract tests (8 checks)
python -m pytest tests/test-companion-host.py -v

# FFmpeg companion safety tests (4 checks)
python tests/test-companion.py

# 20-Fixture Real Browser Matrix E2E Test Suite (20 checks)
python tests/test-e2e-matrix.py
```

---

## Packaging

Build the deterministic, standard-library Chrome Web Store release package:

```sh
python scripts/package.py
```

Produces: `KNOuX-GrabFlow-CHROME-v0.6.0.zip`

---

## Known Boundaries & Honest Disclosures

- **DRM & Access Restrictions:** KNOuX GrabFlow does NOT circumvent DRM, Widevine, PlayReady, FairPlay, paywalls, or authentication gates. Protected streams are accurately classified as unsupported.
- **YouTube:** By product policy and Chrome Web Store policies, YouTube media is excluded from the scanner.
- **Native Companion Requirement:** HLS/DASH adaptive streams cannot be saved as unified movie files via Chrome Downloads API alone; they require the KNOuX Native Companion or a local FFmpeg remux command.
