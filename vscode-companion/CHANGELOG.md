# Changelog

## 0.6.7

- Align the extension version with KNOuX GrabFlow 0.6.7.
- Bundle `assemble_stream.py` and `companion_host.py` in the VSIX so stream
  assembly no longer depends on a repository checkout.
- Resolve the helper from an explicit absolute setting, then the bundled script,
  then the repository checkout used during development.
- Pass an absolute FFmpeg path and use an absolute output path chosen in a Save
  dialog; never rely on the extension host's working directory or inherited PATH.
- Add icon, license, repository/homepage, keyword and package-file metadata.
- Add `knouxGrabflow.companionScriptPath` and mark untrusted workspaces as
  unsupported.
- Correct the README dependency claim: Python, FFmpeg and FFprobe are local
  prerequisites; only the Python helper scripts are bundled.

## 0.6.0

- Initial internal companion extension with Inspect, Assemble and Copy FFmpeg
  Command actions.
