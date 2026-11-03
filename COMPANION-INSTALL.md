# KNOuX GrabFlow — Native Companion Installation Guide

The Native Companion enables adaptive-stream (HLS/DASH) assembly via FFmpeg.  
It is **optional** — direct-file downloads work without it.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Windows 10 / 11 | 64-bit |
| Python 3.9+ | https://python.org — add to PATH during install |
| FFmpeg | https://ffmpeg.org/download.html — add `ffmpeg.exe` to PATH |
| KNOuX GrabFlow | Loaded in Chrome as an unpacked extension (Developer Mode) |

---

## Step 1 — Clone the Repository

```powershell
git clone https://github.com/daynightae-cmyk/KNOuX-GrabFlow.git
cd KNOuX-GrabFlow
```

Or download and extract the source ZIP from the GitHub releases page.

---

## Step 2 — Load the Extension in Chrome

1. Open `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select the `KNOuX-GrabFlow` folder
5. Note the **Extension ID** shown under the extension card

---

## Step 3 — Register the Native Companion

Open PowerShell (no administrator rights needed):

```powershell
cd D:\path\to\KNOuX-GrabFlow
python scripts\register_companion.py
```

The script will:
- Auto-detect your Extension ID from the Chrome profile
- Write `scripts\com.knoux.grabflow.companion.json` with correct paths
- Register the manifest in `HKCU\Software\Google\Chrome\NativeMessagingHosts`

> **Tip:** If Chrome cannot find the companion after registration, restart Chrome.

---

## Step 4 — Verify the Connection

1. Click the KNOuX GrabFlow toolbar icon
2. The companion status pill in the top-right of the popup should show **● Companion ready**
3. Navigate to a page with an HLS or DASH stream
4. Select the stream in GrabFlow → click **Assemble**

---

## Companion Security Properties

- No shell interpolation — FFmpeg is invoked via argument array only
- SSRF protection — `file://`, `localhost`, private IP ranges are blocked
- No credential harvesting — authentication headers are not logged
- No-clobber — existing output files are never overwritten silently
- Restricted to the approved Extension ID — other callers are rejected
- Output directory is restricted to user's Downloads folder

---

## Uninstalling the Companion

```powershell
python scripts\register_companion.py --uninstall
```

This removes the registry key. No system files are modified.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Pill shows "Companion not found" | NM not registered | Re-run `register_companion.py` |
| Assemble fails immediately | FFmpeg not in PATH | Add FFmpeg `bin/` folder to PATH |
| "Stream not supported" | DRM-protected content | Expected — DRM bypass is not implemented |
| Assembly stops at 0% | Stream requires authentication | Use a stream URL accessible without credentials |

---

## Manual Registration (Advanced)

If the script cannot auto-detect your Extension ID, edit `scripts\com.knoux.grabflow.companion.json`:

```json
{
  "name": "com.knoux.grabflow.companion",
  "description": "KNOuX GrabFlow Native Media Companion",
  "path": "C:\\path\\to\\KNOuX-GrabFlow\\scripts\\companion_host.py",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://YOUR_EXTENSION_ID_HERE/"
  ]
}
```

Then register manually:

```powershell
reg add "HKCU\Software\Google\Chrome\NativeMessagingHosts\com.knoux.grabflow.companion" /ve /t REG_SZ /d "C:\path\to\scripts\com.knoux.grabflow.companion.json" /f
```
