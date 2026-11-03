# v0.2.0 validation record

Commands exercised locally in the isolated build container:
- `node --check popup.js scan-page.js asset-utils.js` (run individually): PASS syntax
- `node tests/test-scanner.cjs`: **13/13 passed** (scanner DOM normalization, dedupe, lazy images, CSS, direct links, YouTube guard, cap, URL credentials, dimensions)
- `node tests/test-utilities.cjs`: **6/6 passed** (sort, size filtering, search, safe filenames, CSV, MV3 permissions)
- `python tests/test-ui-inmemory.py`: **PASS** (Chromium in-memory popup; mocked Chrome API: filtering, sorting, download API call, CSV, RTL, no JS errors)
- `python tests/test-ui.py`: **NOT PASSING IN CONTAINER** because localhost navigation yields `ERR_BLOCKED_BY_ADMINISTRATOR`. This is an environment limitation, not proof that real Chrome extension runs.

**Not verified:** actual `chrome://extensions` install, live downloading / file completion, real extension site permissions, store upload, production desktop screenshot. CI status should be checked on GitHub after push.
