#!/usr/bin/env python3
"""Deterministic, reviewable Chrome Web Store zip — standard library only."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_STORED
import json
import os
import sys

ROOT=Path(__file__).resolve().parent.parent
MANIFEST=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
if MANIFEST['manifest_version'] != 3:
    sys.exit('Chrome Manifest V3 required')
FILES=['manifest.json','popup.html','popup.css','popup.js','scan-page.js','asset-utils.js',
       'icons/icon16.png','icons/icon48.png','icons/icon128.png']
for name in FILES:
    if not (ROOT/name).is_file() or (ROOT/name).is_symlink():
        sys.exit(f'Missing/unsafe: {name}')
DEST=Path(os.environ.get("KNOUX_GRABFLOW_PACKAGE_DIR", str(ROOT.parent))).resolve()
if not DEST.is_dir():
    sys.exit(f"Package destination does not exist: {DEST}")
OUT=DEST/f"KNOuX-GrabFlow-CHROME-v{MANIFEST['version']}.zip"
if OUT.exists() and os.environ.get("KNOUX_GRABFLOW_PACKAGE_DIR"):
    sys.exit(f"Refusing to overwrite an existing release artifact: {OUT}")
with ZipFile(OUT,'w',ZIP_STORED) as archive:
    for name in FILES:
        info=ZipInfo(name,(2026,1,1,0,0,0));info.compress_type=ZIP_STORED
        info.create_system=3 # fixed POSIX metadata across Windows/Linux
        info.external_attr=0o644 << 16
        data=(ROOT/name).read_bytes()
        if name.endswith(('.html','.css','.js','.json')):
            data=data.replace(b'\r\n',b'\n') # canonical text payloads across platforms
        archive.writestr(info,data,compress_type=ZIP_STORED)
with ZipFile(OUT) as archive:
    if archive.testzip() is not None: sys.exit('Archive CRC error')
    if sorted(archive.namelist()) != sorted(FILES): sys.exit('Unexpected release file set')
print(f'PACKAGED {OUT} ({OUT.stat().st_size} bytes, {len(FILES)} files)')
