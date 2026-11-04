# KNOuX GrabFlow v0.6.3 — Test Report (Full Edition, Microsoft Edge)

Executed on the development device on 2026-11-04. Every number below is copied from command
output, not restated from a plan. Nothing in this report is a claim about the store, and no
"Full Release" is asserted here.

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
| `tests/test-utilities.cjs` | **18 checks passed** (was 17; 1 new) |
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

## Packaging

`python scripts/package.py`:

```
PACKAGED D:\KNOUX-Workspace\KNOuX-GrabFlow-CHROME-v0.6.3.zip (163547 bytes, 12 files)
PACKAGED D:\KNOUX-Workspace\KNOuX-GrabFlow-EDGE-v0.6.3.zip   (163547 bytes, 12 files)
VERIFIED KNOuX-GrabFlow-CHROME-v0.6.3.zip b855ee03faadef818b86f86c198a60f8fef0e5ccb917226b6b8e467e12fdfccd
VERIFIED KNOuX-GrabFlow-EDGE-v0.6.3.zip   b855ee03faadef818b86f86c198a60f8fef0e5ccb917226b6b8e467e12fdfccd
```

The script now refuses to package unless `default_locale` is declared while locales ship and the
service worker is registered, and re-reads its own checksum file to confirm every digest.

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
8. **The Edge test's own step 9 was invalid** — it acted on discovery rows while the popup was in
   Download Manager view, and it re-seeded assets without their `name`. It only surfaced once the
   `[hidden]` fix above made hidden panels genuinely hidden, which is the correct behaviour.

## Not verified, stated plainly

- Microsoft Partner Center enrolment, submission and review ID: untouched.
- The physical toolbar click and the `activeTab` grant it provides. Automation cannot press a
  toolbar button, so `scan()` in Edge returned no assets and the test fell back to running the
  shipped `scanPageAssets` function inside the page. Detection is verified against real markup;
  the grant path is not.
- Edge browser→native→Edge live assembly on a real device. The companion is not registered here.
- Large-file behaviour beyond a 24-second / 1.5 MB fixture. The ceilings are unit-exercised, not
  stress-tested against multi-gigabyte streams.
- Any accessibility claim: contrast, focus order and screen-reader behaviour were not measured.
