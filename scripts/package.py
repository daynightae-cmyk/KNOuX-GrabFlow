#!/usr/bin/env python3
"""Deterministic, reviewable Chrome/Edge Web Store zips — standard library only.

Both browsers consume the same Manifest V3 payload; Edge is packaged
separately so store submissions and QA artifacts stay unambiguous.
"""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_STORED
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
if MANIFEST['manifest_version'] != 3:
    sys.exit('Manifest V3 required')

FILES = [
    'manifest.json', 'popup.html', 'popup.css', 'popup.js', 'scan-page.js',
    'asset-utils.js', 'background.js',
    'icons/icon16.png', 'icons/icon48.png', 'icons/icon128.png',
    '_locales/en/messages.json', '_locales/ar/messages.json',
]
for name in FILES:
    if not (ROOT/name).is_file() or (ROOT/name).is_symlink():
        sys.exit(f'Missing/unsafe: {name}')

# The manifest promises these two things; refuse to package if they drift.
if MANIFEST.get('default_locale') != 'en':
    sys.exit('manifest.json must declare default_locale "en" while locales are shipped')
if MANIFEST.get('background', {}).get('service_worker') != 'background.js':
    sys.exit('manifest.json must register background.js as the service worker')

DEST = Path(os.environ.get("KNOUX_GRABFLOW_PACKAGE_DIR", str(ROOT.parent))).resolve()
if not DEST.is_dir():
    sys.exit(f"Package destination does not exist: {DEST}")

VERSION = MANIFEST['version']

# Store manifest limits. Edge rejected a real submission with
# "The string KNOuX GrabFlow has exceeded the maximum length of 12" on
# short_name, and the description was over the 132 limit in both locales. These
# are hard package-validation rules, so they are enforced here rather than
# discovered in a dashboard after upload.
STORE_LIMITS = {'name': 75, 'short_name': 12, 'description': 132}


def validate_store_manifest():
    problems = []
    short_name = MANIFEST.get('short_name', '')
    if len(short_name) > STORE_LIMITS['short_name']:
        problems.append(
            f"short_name is {len(short_name)} chars, limit {STORE_LIMITS['short_name']}: {short_name!r}")
    default_locale = MANIFEST.get('default_locale')
    if not default_locale:
        problems.append('default_locale is required while _locales are shipped')
    locales_root = ROOT / '_locales'
    locale_dirs = sorted(p.name for p in locales_root.iterdir() if p.is_dir()) \
        if locales_root.is_dir() else []
    if default_locale and default_locale not in locale_dirs:
        problems.append(f'default_locale {default_locale!r} has no _locales directory')
    for locale in locale_dirs:
        path = locales_root / locale / 'messages.json'
        if not path.is_file():
            problems.append(f'{locale}: messages.json is missing')
            continue
        messages = json.loads(path.read_text(encoding='utf-8'))
        for key, limit_key in (('appName', 'name'), ('appDesc', 'description')):
            value = ((messages.get(key) or {}).get('message') or '').strip()
            if not value:
                problems.append(f'{locale}: {key} is empty')
                continue
            limit = STORE_LIMITS[limit_key]
            if len(value) > limit:
                problems.append(
                    f'{locale}: {key} is {len(value)} chars, limit {limit} ({len(value) - limit} over)')
    return problems


store_problems = validate_store_manifest()
if store_problems:
    print('STORE MANIFEST VALIDATION FAILED:', file=sys.stderr)
    for problem in store_problems:
        print(f'  - {problem}', file=sys.stderr)
    sys.exit(1)
print('STORE MANIFEST VALIDATION OK '
      f"(short_name {len(MANIFEST.get('short_name', ''))}/{STORE_LIMITS['short_name']}, "
      f"locales: {', '.join(sorted(p.name for p in (ROOT / '_locales').iterdir() if p.is_dir()))})")


def build(target_name: str) -> Path:
    out = DEST / f"{target_name}-v{VERSION}.zip"
    if out.exists() and os.environ.get("KNOUX_GRABFLOW_PACKAGE_DIR"):
        sys.exit(f"Refusing to overwrite an existing release artifact: {out}")
    with ZipFile(out, 'w', ZIP_STORED) as archive:
        for name in FILES:
            info = ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_STORED
            info.create_system = 3  # fixed POSIX metadata across Windows/Linux
            info.external_attr = 0o644 << 16
            data = (ROOT/name).read_bytes()
            if name.endswith(('.html', '.css', '.js', '.json')):
                data = data.replace(b'\r\n', b'\n')  # canonical text payloads
            archive.writestr(info, data, compress_type=ZIP_STORED)
    with ZipFile(out) as archive:
        if archive.testzip() is not None:
            sys.exit(f'Archive CRC error in {out.name}')
        if sorted(archive.namelist()) != sorted(FILES):
            sys.exit(f'Unexpected release file set in {out.name}')
    return out


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


artifacts = [build('KNOuX-GrabFlow-CHROME'), build('KNOuX-GrabFlow-EDGE')]
for artifact in artifacts:
    print(f'PACKAGED {artifact} ({artifact.stat().st_size} bytes, {len(FILES)} files)')

checksums = ROOT / f'RELEASE_CHECKSUMS-v{VERSION}.sha256'
if os.environ.get("KNOUX_GRABFLOW_PACKAGE_DIR") and checksums.exists():
    sys.exit(f"Refusing to overwrite an existing checksum file: {checksums}")
lines = [f"{digest(a)}  {a.name}" for a in artifacts]
checksums.write_text("\n".join(lines) + "\n", encoding='utf-8')
print(f'CHECKSUMS {checksums}')

# Re-read and re-verify rather than trusting what was just written: a release
# manifest that does not match its own archives must fail the build here.
for line in checksums.read_text(encoding='utf-8').strip().splitlines():
    expected, _, name = line.partition('  ')
    target = DEST / name
    if not target.is_file():
        sys.exit(f'Checksum references a missing artifact: {name}')
    actual = digest(target)
    if actual != expected:
        sys.exit(f'Checksum mismatch for {name}: {actual} != {expected}')
    print(f'VERIFIED {name} {actual}')
