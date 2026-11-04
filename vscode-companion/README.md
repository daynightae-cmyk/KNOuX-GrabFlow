# KNOuX GrabFlow - VS Code Media Companion

A local developer companion for the KNOuX GrabFlow browser extension. Inspect
HLS/DASH manifests with FFprobe, assemble a stream with local FFmpeg, or copy a
safe FFmpeg command without leaving VS Code.

This extension is **not published on the VS Code Marketplace**. The repository is
private; publication requires the owner to confirm repository visibility and the
proprietary licence terms in `LICENSE.txt`.

## Requirements

- VS Code 1.75 or newer.
- **Python 3.8+** on the local machine. Windows installations under
  `%LOCALAPPDATA%\Programs\Python`, `%ProgramFiles%\Python` and
  `%ProgramFiles(x86)%\Python` are detected automatically. Otherwise set
  `knouxGrabflow.pythonPath` to an absolute `python.exe`.
- **FFmpeg and FFprobe** on the local machine. Set `knouxGrabflow.ffmpegPath` and
  `knouxGrabflow.ffprobePath` to absolute executables, or install them in a
  common location / on the parent `PATH`, where the extension can resolve them to
  an absolute path.

FFmpeg, FFprobe, Python, the browser extension and the Windows native-messaging
host are **not** bundled. The VSIX bundles only the Python helper scripts.

Some package managers expose FFmpeg through a symbolic link (for example the
WinGet `Links` directory or a Homebrew `bin` directory). The companion refuses a
symlinked FFmpeg by design; point `knouxGrabflow.ffmpegPath` at the real file if
your installation is linked.

## Features

- **Inspect Stream / Media URL** probes the URL with local FFprobe through an
  argument array, with no shell. Track codecs, resolution, bit rate and duration
  are written to the `KNOuX GrabFlow` output channel.
- **Assemble HLS/DASH Stream via Companion** runs the bundled
  `companion/assemble_stream.py` with local FFmpeg. The helper performs the same
  nested-reference audit as the native host, restricts the protocol and playlist
  extension whitelist, refuses to overwrite an existing output, and blocks
  loopback/private targets by default. The VS Code command does not pass
  `--allow-local`; that flag exists for controlled tests only.
- **Copy FFmpeg Assembly Command** copies a stream-copy command using
  `-hide_banner -nostdin -c copy -movflags +faststart`.

## Commands

| Command | Title |
|---------|-------|
| `knouxGrabflow.inspectMedia` | KNOuX GrabFlow: Inspect Stream / Media URL |
| `knouxGrabflow.assembleStream` | KNOuX GrabFlow: Assemble HLS/DASH Stream via Companion |
| `knouxGrabflow.generateFfmpegCommand` | KNOuX GrabFlow: Copy FFmpeg Assembly Command |

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `knouxGrabflow.ffmpegPath` | `ffmpeg` | Absolute path, or a bare name resolved to an absolute path. |
| `knouxGrabflow.ffprobePath` | `ffprobe` | Absolute path, or a bare name resolved to an absolute path. |
| `knouxGrabflow.pythonPath` | empty | Absolute Python interpreter; empty uses auto-detection. |
| `knouxGrabflow.companionScriptPath` | empty | Optional absolute `assemble_stream.py`. Empty uses the bundled script, then a repository checkout. |

## Security and scope

- Subprocesses use argument arrays, never `shell: true` or string interpolation.
- Tools are resolved to absolute paths before spawn. The child receives a fixed
  `PATH` containing only the interpreter's directory, plus the environment
  variables Python and FFmpeg need.
- `companion_host.py` must sit next to `assemble_stream.py`; the extension
  refuses to run the helper if the audit module is missing.
- No telemetry, analytics, account, credential collection or KNOuX upload. Only
  the URL you enter is probed or fetched, and output remains on your machine.
- The commands do not bypass DRM, paywalls or access controls. Use them only for
  media you are authorised to access.

## Building the VSIX

From the repository root:

```powershell
python scripts/package-vscode.py
```

The script stages only the runtime files, copies the two Python helpers from
`scripts/`, packages with `@vscode/vsce`, lists the VSIX contents, and records its
SHA-256. The generated VSIX is written to `dist/` and is not committed.

## Verification boundary

`tests/test-vscode-companion.cjs` validates package metadata, command
contributions, bundled-helper contract and path-resolution source shape. Real
extension-host activation is recorded separately in the release test report; a
VSIX being present is not evidence of Marketplace publication.
