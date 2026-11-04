# KNOuX GrabFlow — Full Edition release notes

**Status: upload-ready release candidate with real Edge 156 runtime evidence and a passing store-manifest validation. Not a store-approved release.**

Current version: **0.6.6**. Earlier candidates (0.6.4, 0.6.5) were superseded before any publication, each because a packaged file changed after the previous version had been hashed. Version labels are never reused for different bytes. The v0.6.3 engineering build was merged as `dc7b0fd`; source then changed to close the
SonarCloud findings, then to fix the store manifest limits, so the version moved with the bytes
each time. See `TEST-REPORT-EDGE-FULL.md` for the exact artifact provenance.

Baseline: `main` at `0f836e6a4e160b2b0f8f921a2ca9cc7bcd66c56f` (v0.6.1 tracked source).
This branch reconciles the v0.6.2 Edge QA candidate into the tracked source and advances it.

## What actually changed

### Architecture
- **New MV3 service worker (`background.js`).** It owns the download lifecycle and the native
  companion session. Before this change `chrome.downloads.onChanged` lived in the popup, so
  progress, completion and failure reporting stopped the moment the popup closed. Verified on
  real Edge: a download started, the popup closed entirely, and the reopened popup still showed
  the completed job (`EDGE_PROGRESS_SURVIVES_POPUP_CLOSE`).
- **Persistent native messaging port replaces one-shot `sendNativeMessage`.** The old call could
  not report progress and its host process died with the popup, which is why the Cancel button
  was hard-disabled with the tooltip "needs a persistent host session". It now has one.
- Job store is bounded (80 records, oldest finished dropped) and terminal states are flushed to
  `chrome.storage.local` immediately rather than on the 400 ms throttle, so a worker suspended
  right after completion does not lose the result.
- If the worker is unreachable, the popup degrades explicitly: downloads still start and are
  tracked in that window, and a notice states that progress needs the popup open.

### Native companion (FFmpeg)
- **Real assembly progress.** FFmpeg runs with `-progress pipe:1`; the host parses `total_size`
  and `out_time_us` and streams `assemble_progress` frames. Measured: 4–5 frames with real byte
  counts and percentages during a 24-second HLS assembly.
- **Real cancellation.** Assembly moved to a worker thread, so `cancel` terminates the live
  FFmpeg process. Verified mid-flight: `status=cancelled`, and the job card reflects it.
- **Nested-request SSRF audit.** The manifest is now fetched by the host itself — pinned to a
  previously validated address, with every redirect hop re-validated — and every nested
  reference (`EXT-X-KEY URI`, `EXT-X-MAP`, `SOURCEURL`, DASH `BaseURL`, bare segment lines) is
  validated before FFmpeg is started. A master playlist whose key or segment points at a private
  address is refused; verified with a mocked DNS-rebinding answer.
- **FFmpeg confinement.** `-protocol_whitelist file,http,https,tcp,tls,crypto` and
  `-allowed_extensions` prevent a hostile playlist from reaching local files or arbitrary
  transports. `-rw_timeout`, `-nostdin` and `-n` (no-clobber) are retained.
- **Hard ceilings, enforced not advisory:** 10 MiB inbound frame, 4 MiB manifest body,
  20 000 nested entries, 5 redirect hops, 8 GiB output (job aborted past it), 4 concurrent
  assemblies, 3600 s default timeout.
- **`probe` is now wired to the UI.** The host implemented `handle_probe` since v0.5 and nothing
  ever called it. Streams now show real ffprobe duration, bitrate, tracks and a DRM suspicion
  flag instead of guessed metadata.
- Binary discovery honours `KNOUX_FFMPEG_EXE`, `KNOUX_FFPROBE_EXE` and `KNOUX_FFMPEG_DIR` for
  portable installs. These are environment inputs; a browser message can never set them, and the
  existing refusal of a browser-supplied `allowLocal` is unchanged and still tested.
- Local/loopback media stays blocked by default. A test harness opts in through
  `KNOUX_GRABFLOW_ALLOW_LOCAL=1`, and the host reports which policy is active.

### Edge
- `register_companion.py` registered **only** `Software\Google\Chrome\NativeMessagingHosts`.
  Edge keeps its own hive, so the companion was unreachable in Edge no matter what the user
  installed. Registration now covers Chrome and Edge (`--browser chrome|edge|both`, default both).
- Packaging produces `KNOuX-GrabFlow-EDGE-v0.6.3.zip` alongside the Chrome zip, with the same
  deterministic file set and a self-verifying `RELEASE_CHECKSUMS-v0.6.3.sha256`.
- `tests/test-edge-runtime.py` runs against the installed branded Edge. It resolves the unpacked
  extension ID from the UTF-16LE path hash that Edge actually uses and confirms it against the
  profile's own extension store, because `edge://extensions` renders no usable DOM headless.

### Detection
- Resource-timing buffer is raised to 3000 before reading; Chrome stops recording at ~250 entries
  by default, which is exactly when a media page has fetched its manifest.
- The browser's own `initiatorType` is recorded and shown, so audio and documents fetched by a
  player are classified by fact rather than by file-name guessing.
- Resource timing now yields audio and documents too, not only video.
- New DOM sources: `link rel=preload` (`as=video|audio|image`, and bare `.m3u8`/`.mpd`),
  `object[data]`, `embed[src]`.
- Optional live watch: a bounded MutationObserver counts media-bearing DOM changes after the scan
  and tells the user to refresh. It does not auto-download and it disconnects on toggle.
- YouTube host refusal is unchanged and now also covers the new resource-timing and object paths.

### Visual identity
- Icons are derived from the supplied orb mark by `scripts/build-icons.py` (16/32/48/128 plus a
  512 store tile), committed so packaging never depends on Pillow being present.
- `popup.css` rebuilt as a three-layer token system — primitive, semantic, component — with the
  cyan → violet neon identity of the mark on a deep indigo field. Rules reference tokens, not
  raw hex.
- Layout uses CSS logical properties, so Arabic RTL needs no second stylesheet.
- `tests/test-utilities.cjs` gained a guard that caught a real regression during this work:
  `.view-panel { display: flex }` outranked the UA `[hidden]` rule and stacked the scanner and
  Download Manager together in Edge. The guard fails if the class sets `display` without a
  matching `[hidden]` override.
- The version badge reads `chrome.runtime.getManifest().version` instead of a hard-coded string.

## What was deliberately not done
- No host permissions, no `optional_permissions`, no `webRequest` or `declarativeNetRequest`.
  The least-privilege contract in `PRIVACY.md` and the manifest tests is intact; the manifest test
  now asserts the worker holds no traffic-observation code, replacing the old
  `background === undefined` assertion rather than deleting it.
- No DRM circumvention, no cookie access, no telemetry, no upload endpoint.
- Nothing was removed. No branch, worktree or feature was deleted; the Direct-only candidate and
  the untracked `v0.6.2/` release metadata are untouched.

### Live Edge to native assembly
`tests/test-edge-native-e2e.py` registers the host for Edge only, drives the branded Edge
extension to a real handshake, starts an assembly from the shipped UI, reads progress from the
shipped Download Manager DOM, and ffprobes the produced file: 1 042 878 bytes, 16.04 s, video +
audio. Registry key and generated launcher are removed afterwards, and the test refuses to run if
a companion host is already registered. `register_companion.py` gained `--env NAME=VALUE` so a
portable FFmpeg install can be recorded in the launcher at registration time. This surfaced and
fixed the `master.m3u8.mp4` naming defect.

## Gates still open before any Full Release claim
- Microsoft Partner Center enrolment, submission and review ID are unverified.
- The physical toolbar click and the `activeTab` grant it provides cannot be exercised by
  automation; discovery is verified by running the shipped scanner function, not by a fixture list.
- Third-party CDN streams are untested: the live assembly used a local fixture with loopback
  deliberately relaxed and reported by the host.
- Store-listing assets and screenshots need refreshing for the new identity.
