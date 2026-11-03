# KNOuX GrabFlow v0.3.0 — Verification ledger

Branch: `feature/grabflow-v0.3-audio-hardening`
Base main: `408a67e1b8e6010353f0f85a49f65e9ed51dbca8`.

| Test / gate | Result | Evidence |
|---|---|---|
| JavaScript syntax | PASS | `node --check scan-page.js popup.js asset-utils.js` run separately |
| DOM scanner/security | PASS (18/18) | `node tests/test-scanner.cjs` |
| Filename/filters/CSV/security | PASS (7/7) | `node tests/test-utilities.cjs` |
| Browser popup with mock Chrome APIs | PASS in model's local Chromium | `python tests/test-ui-inmemory.py` |
| Windows packaging | PASS | `py scripts/package.py`, ZIP 9 files |
| GitHub Actions | PENDING when authored | Commit/PR SHA-specific CI required |
| Real extension install and toolbar scan | NOT VERIFIED | Needs browser-side QA on Windows |
| Real direct downloads complete | NOT VERIFIED | A successful download ID is not completion |
| Chrome Web Store listing | NOT SUBMITTED | Requires legal/privacy/listing QA and approval |

Security limitations: only HTTP(S) URL extraction; excludes credentials, page special schemes and DRM/YouTube video flows; no external code, analytics, or background scripts. Never label released solely because CI passes.
