#!/usr/bin/env python3
"""Assemble the v0.6.7 store submission bundle without contacting any store.

The bundle is a convenience copy for a human operator. It is not evidence of a
submission, approval or publication. Existing files are never replaced with
different bytes.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
VERSION = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))["version"]
EXPECTED_HASH = "313f4d2c4b62fb8304af173198814218caec6cc9f92df4de2bbb2ab0b713e028"
ASSETS = ROOT / "store-assets" / VERSION
ASSET_MANIFEST = "ASSET_SHA256.json"
PACKAGES_DIR = "packages"
PACKAGES = ["KNOuX-GrabFlow-CHROME-v0.6.7.zip", "KNOuX-GrabFlow-EDGE-v0.6.7.zip"]
ASSET_FILES = [
    "GrabFlow-v0.6.7-English-1280x800.png",
    "GrabFlow-v0.6.7-Arabic-RTL-1280x800.png",
    "GrabFlow-v0.6.7-Direct-Video-1280x800.png",
    "GrabFlow-v0.6.7-Promo-440x280.png",
    "GrabFlow-v0.6.7-Marquee-1400x560.png",
    "GrabFlow-v0.6.7-Logo-300x300.png",
    "GrabFlow-v0.6.7-Icon-128x128.png",
    ASSET_MANIFEST,
]
DOCS = [
    ("STORE_SUBMISSION-v0.6.7.md", ROOT / "STORE_SUBMISSION-v0.6.7.md"),
    ("PRIVACY.md", ROOT / "PRIVACY.md"),
    ("TEST-REPORT-v0.6.7.md", ROOT / "TEST-REPORT-v0.6.7.md"),
]

UPLOAD_README = """KNOuX GrabFlow v0.6.7 - store submission bundle
=================================================

Status: PREPARED, NOT SUBMITTED, NOT APPROVED, NOT PUBLISHED.

Read STORE_SUBMISSION-v0.6.7.md first. It contains the listing copy, permission
justifications, privacy answers, review notes, checklists and explicit
non-claims for both Chrome Web Store and Microsoft Edge Add-ons.

Contents
--------
packages/KNOuX-GrabFlow-CHROME-v0.6.7.zip
packages/KNOuX-GrabFlow-EDGE-v0.6.7.zip
packages/SHA256SUMS-packages.txt
assets/ (three 1280x800 screenshots, promo, marquee, logo, icon, manifest)
STORE_SUBMISSION-v0.6.7.md
PRIVACY.md
TEST-REPORT-v0.6.7.md
SHA256SUMS.txt (every file in this bundle except itself)

Before upload
-------------
1. Verify packages/SHA256SUMS-packages.txt against the two ZIPs.
2. Verify assets/ASSET_SHA256.json against the PNG dimensions and hashes.
3. Confirm the public privacy policy URL in the kit still resolves.
4. Confirm the developer account, fee, 2FA and identity verification for the
   store you are using.
5. Upload only the package for that store. The two ZIPs are byte-identical MV3
   payloads; each is named for its store.

Do not
------
- Do not upload KNOuX-GrabFlow-CHROME-v0.6.2.zip or the v0.6.1 submission kit.
- Do not claim approval or publication until the store shows a public listing.
- Do not add permissions, remote code, analytics or host access to help review.
- Do not bundle FFmpeg, FFprobe, Python or the native host in a browser ZIP.
- Do not treat this bundle as proof that a submission occurred.
"""


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_unchanged(source, target):
    if not source.is_file() or source.is_symlink():
        fail(f"missing or unsafe source: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_bytes() != source.read_bytes():
            fail(f"existing file differs: {target}")
    else:
        shutil.copy2(source, target)


def validate_kit_document():
    kit = (ROOT / f"STORE_SUBMISSION-v{VERSION}.md").read_text(encoding="utf-8")
    if "Status: PREPARED, NOT SUBMITTED, NOT APPROVED, NOT PUBLISHED." not in kit:
        fail("submission kit lost its non-submission status")
    if "v0.6.1" in kit and "Do not upload" not in kit:
        fail("stale v0.6.1 instructions are not clearly rejected")


def require_assets():
    for name in ASSET_FILES:
        if not (ASSETS / name).is_file():
            fail(f"missing asset: {ASSETS / name}")


def copy_packages(packages, output):
    lines = []
    for name in PACKAGES:
        source = packages / name
        if not source.is_file():
            fail(f"missing package: {source}")
        actual = digest(source)
        if actual != EXPECTED_HASH:
            fail(f"package hash differs: {source} {actual}")
        copy_unchanged(source, output / PACKAGES_DIR / name)
        lines.append(f"{actual}  {name}")
    (output / PACKAGES_DIR / "SHA256SUMS-packages.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def copy_assets(output):
    manifest = json.loads((ASSETS / ASSET_MANIFEST).read_text(encoding="utf-8"))
    for name in ASSET_FILES:
        copy_unchanged(ASSETS / name, output / "assets" / name)
        if name == ASSET_MANIFEST:
            continue
        if digest(ASSETS / name) != manifest[name]["sha256"]:
            fail(f"asset hash differs from manifest: {name}")


def write_bundle_checksums(output):
    files = sorted(
        path
        for path in output.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS.txt"
    )
    lines = [f"{digest(path)}  {path.relative_to(output).as_posix()}" for path in files]
    checksum = output / "SHA256SUMS.txt"
    checksum.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return checksum, files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(
            ROOT.parent / "_releases" / f"KNOuX-GrabFlow-v{VERSION}" / "store-submission"
        ),
        help="Destination directory for the assembled bundle.",
    )
    parser.add_argument(
        "--packages",
        default=str(ROOT.parent),
        help="Directory containing the v0.6.7 Chrome and Edge ZIPs.",
    )
    args = parser.parse_args()
    output = Path(args.output).resolve()
    packages = Path(args.packages).resolve()

    validate_kit_document()
    require_assets()

    output.mkdir(parents=True, exist_ok=True)
    (output / PACKAGES_DIR).mkdir(exist_ok=True)
    (output / "assets").mkdir(exist_ok=True)

    copy_packages(packages, output)
    copy_assets(output)
    for name, source in DOCS:
        copy_unchanged(source, output / name)
    (output / "README-UPLOAD.txt").write_text(UPLOAD_README, encoding="utf-8")

    checksum, files = write_bundle_checksums(output)

    print(f"SUBMISSION_ASSEMBLED {output}")
    print(f"SUBMISSION_FILES {len(files) + 1}")
    print(f"SUBMISSION_CHECKSUMS {checksum}")
    print("STATUS PREPARED_NOT_SUBMITTED_NOT_APPROVED_NOT_PUBLISHED")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001 - CLI must print a clear failure
        print("FAIL:", error)
        sys.exit(1)
