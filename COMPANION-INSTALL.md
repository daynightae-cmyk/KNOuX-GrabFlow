# KNOuX GrabFlow - Windows Native Companion Setup

The companion is optional. Direct Chrome file downloads do not require it.
Adaptive HLS/DASH assembly requires locally installed FFmpeg and FFprobe.

## 1. Install the unpacked Chrome extension

1. Go to chrome://extensions and enable Developer mode.
2. Choose Load unpacked and select the repository extension root.
3. Copy the exact 32-letter Extension ID shown on the extension card.
4. Install official FFmpeg binaries and ensure ffmpeg/ffprobe are in PATH.

## 2. Register the Native Messaging host (explicit opt-in)

From a PowerShell window in the GrabFlow checkout:

    python scripts\register_companion.py --extension-id YOUR_32_LETTER_EXTENSION_ID

Or run:

    scripts\install-companion.bat --extension-id YOUR_32_LETTER_EXTENSION_ID

The installer does NOT auto-detect your extension ID. The exact 32-character
ID is mandatory. Wildcards are invalid and rejected by Chrome. Registration
generates a host launcher and manifest under %LOCALAPPDATA%\KNOuX\GrabFlow
and writes a matching HKCU Chrome NativeMessagingHosts registry key. It does
not require administrator rights.

The tracked scripts/com.knoux.grabflow.companion.json is an inert template;
the generated, user-specific manifest is the one registered locally.

## 3. Verify

Restart Chrome. Open an accessible media page, click GrabFlow's toolbar action,
and inspect the companion-status indicator. A successful native ping does NOT
prove that FFmpeg assembly or file integrity is working. Test permitted,
unprotected HLS/DASH streams independently.

## Uninstall

    python scripts\register_companion.py --unregister

This removes the current-user registry key, leaving generated files intact
for inspection. It does not delete any downloaded media.

## Security and known limitations

- The native host permits exactly the extension ID explicitly registered.
- Browser messages cannot override the localhost/private-network restrictions.
- Browser output names resolve beneath the current user's Downloads directory.
- FFmpeg is invoked using an argument list, with no overwrite flag.
- Native Messaging install, live Windows stream assembly, and playback have not
  yet been verified on this device (FFmpeg and FFprobe are missing from PATH).
- DNS rebinding, redirected/private stream segments, and cancel/progress
  lifecycle require further hardening before untrusted stream support.
- Chrome sendNativeMessage launches a distinct native process for every call;
  a separate cancel request cannot reliably stop the previous assembly.

Official Chrome specification:
https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging
