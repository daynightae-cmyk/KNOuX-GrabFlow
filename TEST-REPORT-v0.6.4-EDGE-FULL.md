# KNOuX GrabFlow v0.6.4 — Test Report (Full Edition, Microsoft Edge)

Executed on the development device on 2026-11-04. Every number below is copied from command
output, not restated from a plan. Nothing in this report is a claim about the store, and no
"Full Release" is asserted here.

## Version and artifact provenance

Two builds of this work exist and must not be confused:

| Build | Source | Manifest | Artifact SHA-256 | Status |
|---|---|---|---|---|
| Engineering build | merged as `dc7b0fd` | 0.6.3 | `b8aa2aad20eb61a023a72b2c310a4a157f612d63d14bd0b6c0171b7e1b3cdb5c` (164 471 B) | merged; superseded |
| This report | `release/grabflow-v0.6.3-closure` | **0.6.4** | recorded in the Packaging section below | release candidate |

An earlier report also referenced `b855ee03faadef818b86f86c198a60f8fef0e5ccb917226b6b8e467e12fdfccd`
(163 547 B). That was an interim build produced before the last round of Sonar-driven source
changes; it is neither of the two above.

The version was bumped to **0.6.4** precisely because source changed *after* the 0.6.3 artifacts
had been built and hashed. Keeping the 0.6.3 label would attach new content to an already-recorded
artifact whose bytes no longer match. Published version semantics are never reused here.

## Package scope — what the ZIP does and does not contain

`KNOuX-GrabFlow-CHROME-v0.6.4.zip` and `KNOuX-GrabFlow-EDGE-v0.6.4.zip` contain **the browser
extension only** — 12 files: manifest, popup HTML/CSS/JS, the scanner, asset utilities, the
service worker, three icons and two locale files.

They do **not** contain the native companion host, FFmpeg or FFprobe. Direct media downloads work
from the ZIP alone. HLS/DASH assembly and stream inspection require the separately installed
companion described in `COMPANION-INSTALL.md`, with FFmpeg/FFprobe present. A green native-host
test in this report is evidence about that separate installation, not about the ZIP.

## Device and toolchain

| Component | Measured value |
|---|---|
| Microsoft Edge | `156.0.4314.58` (file version of the branded binary) |
| Playwright | 1.64.1, `channel="msedge"` |
| Node | v24.21.0 |
| Python | 3.14.8 |
| FFmpeg | `N-128352-gec887b13a8-20261103` — portable build, HLS + DASH + http/https/tls confirmed |
| FFprobe | same build |
| Git | 2.56.0.windows.2 |
| Baseline | `main` = `origin/main` = `0f836e6a4e160b2b0f8f921a2ca9cc7bcd66c56f` |

FFmpeg was **not** present on this machine at the start. The bundled Playwright FFmpeg
(`ffmpeg-1013`) is configured `--disable-everything` with only `file`/`pipe` protocols and
VP8/VP9, so it cannot do HLS, DASH or HTTP and was not used as a substitute. A portable GPL
build was fetched into `D:\KNOUX-Workspace\_tools\ffmpeg` — outside the repository, nothing
installed system-wide — and `tests/media_tools.py` now resolves it through
`KNOUX_FFMPEG_DIR` / `KNOUX_FFMPEG_EXE` / `KNOUX_FFPROBE_EXE` so the suites run for real locally
and through `apt` in CI.

## Static and unit suites

| Suite | Result |
|---|---|
| `node --check` popup.js / scan-page.js / asset-utils.js / background.js / vscode-companion | 5/5 OK |
| `tests/test-scanner.cjs` | **36 checks passed** (was 30; 6 new) |
| `tests/test-utilities.cjs` | **19 checks passed** (was 17; 2 new) |
| `tests/test-vscode-companion.cjs` | 2 passed |
| `tests/test-companion-host.py` | Ran 8 — OK |
| `tests/test-native-boundary.py` | Ran 10 — OK |
| `tests/test-companion.py` | Ran 4 — OK |
| `tests/test-stream-integration.py` | PASS — real HLS → playable MP4, 103 663 bytes |
| `tests/test-stream-matrix.py` | Ran 2 — OK (HLS master variant selection + no-clobber; DASH integrity) |

## Real native-messaging protocol test (new)

`tests/test-companion-protocol.py` speaks the length-prefixed protocol to the host as a
subprocess, exactly as the browser does. 24-second HLS fixture, throttled origin so progress and
cancellation are observable mid-flight.

```
[1] PING OK  version=0.6.3 policy=test-relaxed caps=['ping','probe','assemble','assemble-async','progress','cancel']
[2] PROBE OK duration=24.0s video={'width':320,'height':180,'codec':'h264'} audio={'codec':'aac'}
[3] ASSEMBLE STARTED nestedAudit={'status':'passed','checked':12,'hosts':['127.0.0.1']}
[4] PROGRESS FRAMES=4 last={'bytes':1048624,'mediaTimeSeconds':18.04,'percent':75,'elapsedSeconds':4.7}
[5] ASSEMBLE COMPLETE bytes=1563714 percent=100 elapsed=5.4s
[6] OUTPUT VERIFIED playable MP4 video+audio duration=24.032676s
[7] CANCEL VERIFIED job=j2 status=cancelled
[8] STRICT BLOCKED [loopback manifest]:  SSRF protection: access to private/loopback address 127.0.0.1 is blocked
[8] STRICT BLOCKED [non-http scheme]:    Only HTTP and HTTPS media URLs are supported
[8] STRICT BLOCKED [credentials in url]: URLs containing credentials are strictly prohibited
[8] STRICT BLOCKED [not a playlist]:     URL must target an HLS (.m3u8) or DASH (.mpd) stream manifest
[9] POLICY OVERRIDE REJECTED: Network policy cannot be overridden by a browser message
[10] NESTED SSRF BLOCKED: nested media reference rejected — http://internal.corp/key -> ... 127.0.0.1 ...
[11] NESTED PUBLIC ALLOWED: {'checked':1,'blocked':[],'hosts':['cdn.example.test']}
COMPANION_PROTOCOL_TEST: ALL CHECKS PASSED
```

Step [12] drives 2000 stderr lines through the assembly worker and asserts it terminates: `STDERR_DRAINED job finished without deadlock; progress_frames=1 bytes_seen=4096`.

Progress frames carry real byte counts and real media time. Cancel was issued 2 s into a running
assembly and the job ended `cancelled`. Steps 10–11 use a mocked DNS answer where a public
manifest host resolves normally but a nested reference rebinds to loopback.

## Branded Microsoft Edge 156 runtime test (new — the recorded release blocker)

`tests/test-edge-runtime.py`, exit code **0**.

```
EDGE_BINARY: C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
EDGE_VERSION: Microsoft Edge 156.0.4314.58
EDGE_LAUNCH_MODE: headless=new
[1] EDGE_UNPACKED_REGISTERED derived=khjchfbpeoiefclibnoojmkicbaglhei profile_confirmed=khjchfbpeoiefclibnoojmkicbaglhei match=yes
    EDGE_EXTENSION_ORIGIN_LIVE chrome-extension://khjchfbpeoiefclibnoojmkicbaglhei
[2] EDGE_SERVICE_WORKER_ALIVE answered jobs:list jobs=0 popupBridge=True
[3] EDGE_POPUP_RENDERED name='KNOuX GrabFlow — Media & Video Finder' badge='FULL 0.6.3'
    permissions=['activeTab','scripting','downloads','storage','nativeMessaging']
[4] EDGE_REAL_SCAN route=in-page-shipped-scanner total=03 sources=['image','link','video']
      image  None    image  http://127.0.0.1:.../media/emblem.png
      video  direct  video  http://127.0.0.1:.../media/clip.mp4
      video  hls     link   http://127.0.0.1:.../media/stream.m3u8
[5] EDGE_BILINGUAL_RTL_LTR OK
[6] EDGE_REAL_DOWNLOAD discovered=http://127.0.0.1:.../media/emblem.png
    EDGE_DOWNLOAD_BYTES_VERIFIED 30752 bytes SHA256=5e2cb1db90383c0fff02ec4e77019d249b7aa8a319e285248baaea0e7dea1799
    EDGE_WORKER_JOB_TRACKED kind=chrome state=complete size=30752
[7] EDGE_PROGRESS_SURVIVES_POPUP_CLOSE jobs=1 complete=1 cards=1
[8] EDGE_COMPANION_TRUTHFUL pill='COMPANION: NOT INSTALLED'
    state={'connected':False,'missingTools':False,'error':'Specified native messaging host not found.'}
[9] EDGE_MP4_INTEGRITY 65796 bytes duration=2.000000 tracks=['audio','video']
EDGE_RUNTIME_PASS edge=Microsoft Edge 156.0.4314.58 extension=khjchfbpeoiefclibnoojmkicbaglhei v0.6.3
```

Step [1] required solving why the handoff said Edge QA could not complete. `edge://extensions`
renders only a `ROOT-APP` element with an empty body under headless Edge, so scraping it never
works, and Chromium's usual UTF-8 path-hash ID derivation does not match Edge. The ID is derived
from the **UTF-16LE** path hash and confirmed against the profile's own `Secure Preferences`
extension store; both agree here.

Step [2] proves the worker by a message round-trip only the worker can serve (`jobs:list`),
because Playwright does not surface Edge's headless service-worker event.

Step [7] is the behavioural fix: the download was started, the popup page was **closed**, 2 s
passed, a fresh popup opened the Download Manager, and the completed job with its byte count was
still there. That was impossible while the listener lived in the popup.

Step [8] is deliberately an assertion about honesty: the pill reports the real failure string and
the UI claims no assembly capability. The companion is genuinely not registered on this device.

## Chromium MV3 suite

`tests/test-real-mv3.py`, exit **0**:

```
REAL_MV3_UNPACKED_PASS: khjchfbpeoiefclibnoojmkicbaglhei
REAL_CHROME_DOWNLOAD_COMPLETE: 30752 bytes SHA256=5e2cb1db...
REAL_CHROME_MP4_COMPLETE: 68822 bytes SHA256=401ccd2b... video+audio ffprobe=PASS
SERVICE_WORKER_REGISTERED: chrome-extension://.../background.js
WORKER_PERSISTED_JOBS: 2
VERIFIED: extension origin, no-mock browser downloads API, actual PNG+MP4 file bytes, RTL/LTR, service worker job persistence
NOT VERIFIED: physical toolbar action, activeTab grant, HLS/DASH assembly via native messaging
```

`tests/test-e2e-matrix.py`: **ALL 20 FIXTURE MATRIX TESTS PASSED**.
`tests/test-ui.py` and `tests/test-ui-inmemory.py`: PASS, no page errors.

## Live Edge -> native host -> FFmpeg end-to-end (new)

`tests/test-edge-native-e2e.py`, exit **0**. This is the evidence the handoff called missing:
not a Python-side protocol test, but the branded Edge extension talking to a registered
companion host and producing a real file.

```
[0] EDGE_HOST_NOT_PREVIOUSLY_REGISTERED - safe to proceed
[1] DERIVED_EDGE_EXTENSION_ID khjchfbpeoiefclibnoojmkicbaglhei
[2] EDGE_HOST_REGISTERED key=HKCU\Software\Microsoft\Edge\NativeMessagingHosts\com.knoux.grabflow.companion
[3] EDGE_TO_NATIVE_HANDSHAKE version=0.6.3 policy=test-relaxed pill='COMPANION: CONNECTED'
[4] EDGE_LIVE_ASSEMBLY samples=9 with_progress=3 bytes=1042878 nestedAuditChecked=8
      pending             0 B    0%
      in_progress    262192 B   50%
[5] EDGE_PRODUCED_FILE master.mp4 1042878 bytes duration=16.04s tracks=['audio','video']
EDGE_NATIVE_E2E_PASS assembly=verified-by-ffprobe
[6] REGISTRY_KEY_REMOVED + launcher and manifest deleted
```

The pill read `COMPANION: CONNECTED` because the handshake really happened. Progress was read
from the shipped Download Manager DOM, not from an internal variable. The output was probed by
real ffprobe for duration and both track types. The registry key and generated files belong to
this test and were removed afterwards; the test refuses to run if a companion host is already
registered, so a real user installation is never overwritten.

Loopback media was explicitly relaxed for the local fixture via the launcher environment, and the
host reported `policy=test-relaxed`. The shipped default still blocks private addresses, asserted
in the protocol suite.

Running this surfaced a real naming defect: `safeDownloadName` keeps the playlist name for an HLS
asset, so the assembled file was written as **`master.m3u8.mp4`**. The playlist suffix is now
dropped before the media suffix, and `tests/test-companion-host.py` covers it - the rerun produced
`master.mp4`.

## Packaging (v0.6.4 release candidate)

`python scripts/package.py`:

```
PACKAGED D:\KNOUX-Workspace\KNOuX-GrabFlow-CHROME-v0.6.4.zip (165445 bytes, 12 files)
PACKAGED D:\KNOUX-Workspace\KNOuX-GrabFlow-EDGE-v0.6.4.zip   (165445 bytes, 12 files)
VERIFIED KNOuX-GrabFlow-CHROME-v0.6.4.zip 6e9a2b7c99681a39a23e44961c454a6cb77f8b7ace24af8f20d620aea082bf26
VERIFIED KNOuX-GrabFlow-EDGE-v0.6.4.zip   6e9a2b7c99681a39a23e44961c454a6cb77f8b7ace24af8f20d620aea082bf26
```

The two archives are byte-identical because both browsers consume the same Manifest V3 payload;
they are packaged separately only so a store submission and a QA artifact are never confused.

Artifact audit performed on the Edge zip:

| Check | Result |
|---|---|
| ZIP integrity (`zipfile.testzip`) | PASS |
| File count and set | 12 files, exactly the expected list, nothing else |
| Manifest V3 | PASS |
| Declared permissions | `activeTab`, `scripting`, `downloads`, `storage`, `nativeMessaging` |
| `host_permissions` | absent |
| Background service worker | `background.js` |
| Locales | `_locales/en`, `_locales/ar` |
| Icons | 16 / 48 / 128 |
| SHA-256 re-read and verified | PASS |
| Secrets, `.env`, `.pem`, `node_modules`, `.git/`, machine paths | none present |
| Corresponds to the tested source SHA | the closure commit that produced it; see the final delivery |

`RELEASE_CHECKSUMS-v0.6.4.sha256` records both digests and the script re-reads and re-verifies it
before exiting. `RELEASE_CHECKSUMS-v0.6.3.sha256` is left in place as the record of the superseded
merged build.

## Defects found and fixed during this testing

These came out of running the tests, not from reading the code.

1. **Async assembly results were computed and discarded.** The worker thread called
   `_run_job` and threw away its return value, so the browser received one progress frame and then
   nothing — the job hung forever. Found by the new protocol test.
2. **Terminal job states were lost to the write throttle.** A completed download was not in
   `chrome.storage.local` when the popup reopened 400 ms later. Found by `test-real-mv3.py`.
   Terminal states now flush immediately.
3. **The worker never enriched completed downloads.** `onChanged` deltas carry only what changed,
   so `fileSize` and `totalBytes` stayed empty and the manager showed no size. Found by the Edge
   test. Completed downloads are now re-queried once.
4. **`.view-panel { display: flex }` outranked the UA `[hidden]` rule**, so the scanner and the
   Download Manager rendered together. Found by looking at the Edge screenshot. Fixed, and a new
   contract test fails if the pattern returns — verified by re-breaking the CSS and watching the
   test go red.
5. **`popup.html` referenced `icons/icon48.png`**, which the browser-UI harnesses rewrite for
   `icon128.png`; the emblem fell back to alt text. Found in the rendered screenshot.
6. **`shutil.which('ffmpeg')` fails for forward-slash PATH entries** from non-native shells, so
   the stream suites silently SKIPped on this machine and reported nothing. Replaced by an
   explicit resolver that also honours portable builds.

7. **TLS hostname verification was disabled in the pinned socket.** `_pinned_connect` set
   `context.check_hostname = False` while dialling a validated IP. That is a real weakening: a
   valid certificate for *any* host would have been accepted. Passing `server_hostname` is what
   actually handles the IP-vs-name mismatch, so verification is now fully on, and CI has a grep
   gate that fails if `check_hostname = False` or `CERT_NONE` returns. Found by SonarCloud's
   Security Rating on New Code.
9. **FFmpeg stderr was read only after stdout closed.** A pipe holds a limited
   buffer; a real assembly with many failing segments writes more than that and FFmpeg then
   blocks on stderr while we block on stdout — a deadlock that would surface as a hung assembly,
   not an error. stderr is now drained on its own thread into a bounded 40-line ring, which also
   caps memory. `tests/test-companion-protocol.py` step [12] proves it with 2000 warning lines:
   `STDERR_DRAINED job finished without deadlock; progress_frames=1 bytes_seen=4096`.
10. **A framing error in the native protocol would spin the host.** `run_host` caught a short,
    oversized or unparseable frame, replied, and looped — but a length-prefixed stream cannot be
    resynchronised, so it would emit errors forever. It now ends the session after reporting.
11. **Retrying a cancelled or failed assembly wrote the wrong file type.** The retry path
    rebuilt the asset without `type`, and `safeDownloadName` derives the extension from it, so a
    re-assembled HLS job would have been aimed at a `.bin` file. Fixed, and
    `tests/test-utilities.cjs` now asserts the retry branch carries a media type — verified by
    removing it and watching the check go red.
12. **Two `innerHTML` assignments in the shipped popup** were flagged by SonarCloud's Security
    Rating and removed; the empty-state and CORS blocks are built with `createElement`.

8. **The Edge test's own step 9 was invalid** — it acted on discovery rows while the popup was in
   Download Manager view, and it re-seeded assets without their `name`. It only surfaced once the
   `[hidden]` fix above made hidden panels genuinely hidden, which is the correct behaviour.

## SonarCloud findings, read from the API and fixed

With a Sonar token the actual findings became visible: 116 issues on the PR. The two failing
conditions were driven by these, not by the complexity nits:

**Security**
- `python:S5527` on `_pinned_connect`. The code was already correct — `server_hostname` is what
  reconciles dialling an IP with verifying a name — but nothing *stated* the guarantee.
  `check_hostname` and `verify_mode` are now set explicitly and asserted after the handshake, so
  a future regression raises instead of silently accepting a certificate issued to another host.
- `pythonsecurity:S8701` on `assemble_stream.main()`: `--ffmpeg` was handed to subprocess after
  only a "does it exist" check. Added `validate_executable()` requiring an existing regular,
  non-symlink, executable-shaped file. The CLI also now applies the same protocol and extension
  whitelists as the host, so the manual path is not the weaker path.
- `githubactions:S8541`/`S8544`: pip installs in CI were unpinned and allowed source builds.
  Every install is now `--only-binary ":all:"` with an exact version.

**Reliability**
- `python:S5779` × 34: the Edge suite asserted inside a `try` that caught `AssertionError`.
  Behaviour was still correct, but the pattern is fragile; the handler now catches any exception,
  records the type, and exits non-zero.
- `javascript:S9383` × 8: floating promises in `background.js` and `popup.js`. These were real —
  an unhandled rejection in a service worker can take the worker down mid-download. Every one now
  has a rejection handler with a comment on what the fallback means.
- `javascript:S2871`: a locale-dependent `.sort()` in a new scanner assertion, replaced with an
  explicit `localeCompare` comparator.
- `javascript:S6661`, `S3358`, `S6582`, `S7776`, `python:S5713`, `S8513`, `S1192`, `css:S9423`,
  `css:S1874` cleaned where the change was safe.

**A regression my own refactor introduced, caught by running the suite:** extracting a `badge()`
helper collided with `const badge` inside `render()`, putting the name in a temporal dead zone.
Edge failed with `ReferenceError: Cannot access 'badge' before initialization` and the 20-fixture
matrix went red. Renamed to `makeBadge`; both suites pass again. This is the case for executing
the tests rather than trusting a green unit suite.

## SonarCloud: what was still red on `main`, and why

The merged engineering build `dc7b0fd` did **not** pass the main-branch gate, even though its
pull-request check had. That is a real discrepancy, not a reporting artefact: read from the API,

```
new_security_rating  actual=4 (D)  required A   -> ERROR
new_reliability_rating actual=3 (C) required A  -> ERROR
new_maintainability_rating actual=1 (A)         -> OK
new_security_hotspots_reviewed 100%             -> OK
```

The main-branch leak period covered the whole v0.6.3 diff plus pre-existing files, which surfaced
seven issue-class findings — four bugs, three vulnerabilities — that the pull-request analysis had
not attributed to new code:

| Rule | Where | What it was | Fix |
|---|---|---|---|
| `javascript:S9383` ×2 | `popup.js` | Floating promises from async click handlers and a bare `downloadSelected()` call | Every fire-and-forget action goes through one `runAction()` wrapper that reports rejection instead of leaving it unhandled |
| `javascript:S7727` ×2 | `popup.js` | `isDownloadableAsset` passed straight to `.some()` / `.filter()`, so index and array were fed into a one-argument predicate | Explicit arrow wrappers |
| `javascript:S4036` | `vscode-companion/extension.js` | Child process inherited the caller's `PATH`; a planted `python.exe` / `ffprobe.exe` earlier in `PATH` would have been executed | Tools are resolved to absolute paths; the child gets a fixed `PATH` containing only the tool's own directory, plus the handful of variables it actually needs. `pythonPath` setting added |
| `pythonsecurity:S8705` | `scripts/assemble_stream.py` | `--url` / `--ffmpeg` flowed from argparse into `subprocess` with no last-moment check | `assert_argv_safe()` rejects non-strings, empties, control characters and option-like URLs immediately before launch; `shell=False` is explicit; input is re-checked to be http(s) |
| `javascript:S1523` | `tests/test-scanner.cjs` | `vm.runInNewContext` evaluated the scanner source as a string | The scanner is now a real CommonJS export; the test requires the module and injects the DOM globals it reads. No dynamic evaluation remains anywhere in the test path |

`scripts/assemble_stream.py` also grew `prepare()` to separate validation from execution and keep
`main()` readable.

## Not verified, stated plainly

- Microsoft Partner Center enrolment, submission and review ID: untouched. No store page was
  opened, no account was used, nothing was submitted. `STORE_SUBMISSION = NOT SUBMITTED`,
  `STORE_APPROVAL = NOT VERIFIED`.
- A **third-party public CDN** stream. The live Edge→native→FFmpeg assembly ran against a local
  fixture server with loopback deliberately relaxed for that host, which the host reported as
  `policy=test-relaxed`. The shipping default still blocks private addresses and that refusal is
  asserted in the protocol suite. External-CDN behaviour is therefore not covered.
- The physical toolbar click and the `activeTab` grant it provides. Automation cannot press a
  toolbar button, so `scan()` in Edge returned no assets and the test fell back to running the
  shipped `scanPageAssets` function inside the page. Detection is verified against real markup
  through the shipped code; the permission-grant path itself is UNVERIFIED.
- Large-file behaviour beyond a 24-second / 1.5 MB fixture. The ceilings are unit-exercised, not
  stress-tested against multi-gigabyte streams.
- Any accessibility claim: contrast, focus order and screen-reader behaviour were not measured.
