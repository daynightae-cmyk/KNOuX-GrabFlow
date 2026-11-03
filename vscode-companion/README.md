# KNOuX GrabFlow — VS Code Media Companion

A developer and media engineering companion extension for Visual Studio Code.  
Inspect adaptive streams, validate HLS/DASH playlists, and run KNOuX GrabFlow assembly commands right from your editor.

---

## Features

- **Inspect Stream / Media URL**: Probes stream metadata (tracks, codecs, bitrate, duration) using local FFprobe without leaving VS Code.
- **Assemble HLS/DASH Stream**: Triggers the KNOuX GrabFlow desktop companion (`scripts/assemble_stream.py`) to safely remux streaming segments into a playable MP4/MKV.
- **Copy FFmpeg Command**: Generates and copies ready-to-execute FFmpeg stream-copy commands with safe flags (`-hide_banner -nostdin -c copy -movflags +faststart`).
- **Zero External Dependencies**: Pure Node.js implementation that runs instantly in any VS Code installation.

---

## Commands

| Command | Title | Description |
|---------|-------|-------------|
| `knouxGrabflow.inspectMedia` | Inspect Stream / Media URL | Probe media tracks, codecs, and resolution |
| `knouxGrabflow.assembleStream` | Assemble Stream via Companion | Run local FFmpeg assembly via GrabFlow companion |
| `knouxGrabflow.generateFfmpegCommand` | Copy FFmpeg Assembly Command | Copy safe CLI remux command to clipboard |

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `knouxGrabflow.ffmpegPath` | `ffmpeg` | Custom path to local FFmpeg executable |
| `knouxGrabflow.ffprobePath` | `ffprobe` | Custom path to local FFprobe executable |

---

## Security

- Argument-array subprocess execution: **No shell interpolation**.
- Output path traversal protection: Output filenames validated and confined.
- No network telemetry or credential harvesting.
