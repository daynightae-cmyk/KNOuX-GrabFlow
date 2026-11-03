#!/usr/bin/env python3
"""Deterministic, reviewable Chrome Web Store zip — standard library only."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import json
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
OUT=ROOT.parent/f"KNOuX-GrabFlow-CHROME-v{MANIFEST['version']}.zip"
with ZipFile(OUT,'w',ZIP_DEFLATED,compresslevel=9) as archive:
    for name in FILES:
        info=ZipInfo(name,(2026,1,1,0,0,0));info.compress_type=ZIP_DEFLATED
        info.external_attr=0o644 << 16
        archive.writestr(info,(ROOT/name).read_bytes(),compress_type=ZIP_DEFLATED,compresslevel=9)
with ZipFile(OUT) as archive:
    if archive.testzip() is not None: sys.exit('Archive CRC error')
    if sorted(archive.namelist()) != sorted(FILES): sys.exit('Unexpected release file set')
print(f'PACKAGED {OUT} ({OUT.stat().st_size} bytes, {len(FILES)} files)')
