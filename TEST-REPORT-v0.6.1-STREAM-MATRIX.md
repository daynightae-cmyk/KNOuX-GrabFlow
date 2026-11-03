# KNOuX GrabFlow — Real Windows HLS/DASH Stream Matrix

Date: 2026-11-03 (Asia/Dubai)

## Git boundary
- Canonical repository: https://github.com/daynightae-cmyk/KNOuX-GrabFlow
- Baseline main SHA: `2f941fd1c11da686cc808c5cc8360b3603642183` (v0.6.1)
- Isolated worktree: `D:\KNOUX-Workspace\KNOuX-GrabFlow-stream-matrix-20261103`
- Branch: `feature/grabflow-stream-matrix-20261103`
- Main and other agents' worktrees were not edited.

## Test environment
- Windows, Python 3.14.
- FFmpeg and FFprobe **9.0.1** from Winget-verified `Gyan.FFmpeg.Essentials` archive, extracted to `D:\KNOUX-Workspace\_toolchain\ffmpeg-9.0.1-essentials`.
- Binaries added to PATH for the test shell only. No machine-wide installer, registry registration or profile modification.
- Synthetic media created locally with FFmpeg using video `testsrc2` and audio `sine`, served by an ephemeral local HTTP server.
- The CLI is launched with `--allow-local` **only for these controlled test fixtures**. The native browser-facing host continues to reject browser-supplied `allowLocal`.

## Verification evidence
- Existing `python tests/test-stream-integration.py`: PASS; unencrypted HLS produced 104,134-byte MP4 with video/audio, duration approximately 3 seconds, and FFprobe verification.
- New `python tests/test-stream-matrix.py`: 2/2 PASS after correcting fixture output working directory.
  - HLS master playlist: two declared variants, high variant 160×90 with audio. Output MP4 104,134 bytes; FFprobe duration 3.04 sec, video+audio; SHA256 `94b18eae810041effa674270fac0fbac4f0299af137fd3e301072fa6b0d232cf`.
  - DASH manifest: separate audio/video AdaptationSets. Output MP4 103,453 bytes; FFprobe duration 3.02 sec, video+audio; SHA256 `b28cdd491bbaca87191f96c873a9b42832c3bed54df967f172954bf9ca982fcc`.
  - Repeated assembly into the existing HLS output was rejected and existing file hash remained unchanged.
- `python tests/test-native-boundary.py`: 10/10 PASS on Windows.
- Reproducible fixtures remain ephemeral and are not included in the Chrome ZIP.
- Six segments from the initial failed DASH-fixture experiment were moved, not deleted, to `D:\KNOUX-Workspace\_toolchain_downloads\ffmpeg-essentials\failed-fixture-artifacts-20261103`.

## CI
- The new test is added to `.github/workflows/ci.yml` under `static-and-package` after existing HLS integration.
- CI now requires FFmpeg and FFprobe and exercises two additional real stream-to-file paths before publishing an artifact.
- CI status of this new branch must be evaluated against its exact commit before claiming CI PASS.

## Not verified
- Real Chrome toolbar-click activeTab grant and end-to-end Native Messaging bridge to FFmpeg.
- Native host registration on a real user Chrome profile.
- HLS/DASH content with protected segments, DRM, redirects, changing authentication or remote segment hosts.
- Safe handling of redirects, nested segment SSRF and DNS rebinding.
- A native download queue with true progress/cancellation.
- Store listing or distribution.

## Windows regression sweep after implementation
- JavaScript syntax checks: 4/4 exit 0.
- Scanner/security: 30/30 PASS; utility/security: 17/17 PASS; VS Code contract: 2/2 PASS.
- Python Native Host: 8/8 PASS; Native trust boundary: 10/10 PASS; FFmpeg safety: 4/4 PASS.
- Original real HLS integration: PASS; new stream matrix: 2/2 PASS.
- In-memory popup and localhost browser UI smoke: PASS, each exit 0.
- Browser 20-fixture matrix: 20/20 PASS, exit 0.
- Browser tests regenerated two tracked screenshots; fresh screenshots were preserved at `D:\KNOUX-Workspace\_toolchain_downloads\ffmpeg-essentials\windows-qa-screenshots-20261103`, with their bytes checked and SHA-256 recorded in tool output. Tracked reference screenshots were restored to exact `HEAD` bytes; no unintended visual asset changes are included in the PR.
- No machine-level PATH, user Chrome profile, Git history, previous branches or parallel-agent work was modified.
