# KNOuX GrabFlow — Windows Native Companion Setup

The companion is optional. Direct browser file downloads do not require it.
Adaptive HLS/DASH assembly and stream inspection require locally installed FFmpeg and FFprobe.

## 1. Install the unpacked extension

**Microsoft Edge** (the primary target for v0.6.4):

1. Go to `edge://extensions` and enable Developer mode.
2. Choose *Load unpacked* and select the repository extension root.
3. Copy the exact 32-letter ID shown on the extension card.

**Chrome:** the same three steps at `chrome://extensions`.

Then install official FFmpeg binaries and make sure `ffmpeg` and `ffprobe` are reachable —
either on `PATH`, or through `KNOUX_FFMPEG_DIR` / `KNOUX_FFMPEG_EXE` / `KNOUX_FFPROBE_EXE`
if you use a portable build.

## 2. Register the Native Messaging host (explicit opt-in)

From a PowerShell window in the GrabFlow checkout:

    python scripts\register_companion.py --extension-id YOUR_32_LETTER_EXTENSION_ID

By default this registers **both** browsers. To limit it:

    python scripts\register_companion.py --extension-id ... --browser edge
    python scripts\register_companion.py --extension-id ... --browser chrome

Or run `scripts\install-companion.bat --extension-id YOUR_32_LETTER_EXTENSION_ID`.

If FFmpeg is a portable build rather than on `PATH`, record it in the generated launcher so the
host finds it without depending on a shell environment:

    python scripts\register_companion.py --extension-id ... --env KNOUX_FFMPEG_DIR=D:\tools\ffmpeg\bin

These are local environment inputs written at registration time. A browser message can never set
them, and the host reports which policy and toolchain it resolved.

The installer does NOT auto-detect your extension ID. The exact 32-character ID is mandatory.
Wildcards are invalid and rejected by the browsers. Registration generates a host launcher and
manifest under `%LOCALAPPDATA%\KNOuX\GrabFlow` and writes the matching HKCU keys:

    Software\Google\Chrome\NativeMessagingHosts\com.knoux.grabflow.companion
    Software\Microsoft\Edge\NativeMessagingHosts\com.knoux.grabflow.companion

No administrator rights are required.

> **Why both hives matter.** Until v0.6.3 only the Chrome key was written, so the companion was
> unreachable in Edge no matter what a user installed — the popup could only ever report
> `COMPANION: NOT INSTALLED`. If you upgraded from an earlier build, re-run the registration.

The tracked `scripts/com.knoux.grabflow.companion.json` is an inert template; the generated,
user-specific manifest is the one registered locally.

## 3. Verify

Restart the browser. Open an accessible media page, click GrabFlow's toolbar action, and check the
companion-status indicator. It reports one of four honest states: connected, checking, not
installed, or installed-but-missing-FFmpeg. A successful ping does **not** prove that assembly or
file integrity works. Test permitted, unprotected HLS/DASH streams independently.

Once connected, two things become available on a stream row that were not reachable before:
**Inspect** (real ffprobe duration, bitrate, tracks and a DRM suspicion flag) and **Assemble** with
live byte progress and a working Cancel.

## Uninstall

    python scripts\register_companion.py --unregister

Removes the current-user registry keys for both browsers, leaving generated files intact for
inspection. It does not delete any downloaded media.

## Security posture and remaining limits

Now enforced and covered by tests (`tests/test-companion-protocol.py`):

- The native host permits exactly the extension ID explicitly registered.
- Browser messages cannot override the localhost/private-network restrictions.
- Output names resolve beneath the current user's Downloads directory; no-clobber is enforced.
- FFmpeg is invoked with an argument list, never a shell, and is confined by
  `-protocol_whitelist` and `-allowed_extensions`.
- The manifest is fetched and every nested reference (keys, maps, variants, segments) is
  validated before FFmpeg starts, with redirect hops re-validated and DNS answers pinned.
- Ceilings are enforced on manifest size, nested reference count, output size, concurrent jobs
  and elapsed time.
- Assembly runs on a worker thread, so progress frames are emitted and Cancel genuinely stops the
  live FFmpeg process. Previously `sendNativeMessage` spawned a separate process per call and a
  cancel request could not reach the running assembly.

Still open, and the reason this is not a release claim:

- FFmpeg performs its own segment fetches after the audit; a stream that changes its playlist
  mid-assembly is re-audited only when the host re-reads it. Treat the audit as defence in depth,
  not a guarantee.
- Live Edge browser→native→Edge end-to-end assembly on a real device has not been performed here;
  the Edge run reports the host as not installed, which is the truthful state on that machine.
- DNS rebinding against a media host that re-resolves between audit and FFmpeg connect remains a
  theoretical window; FFmpeg is not pinned to the audited address.

Official specification:
https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging
