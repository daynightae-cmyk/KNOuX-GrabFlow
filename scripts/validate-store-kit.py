#!/usr/bin/env python3
"""Validate the v0.6.7 store submission kit without contacting any store.

Checks:
  * Listing copy stays inside Chrome/Edge field limits.
  * The manifest version/permissions match the release claims.
  * Every generated asset exists with the recorded dimensions and SHA-256.
  * The release checksum file names the expected browser packages and hash.
  * The kit names both stores, the public privacy policy and the non-claims.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import struct
import sys

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_VERSION = "0.6.7"
EXPECTED_HASH = "313f4d2c4b62fb8304af173198814218caec6cc9f92df4de2bbb2ab0b713e028"
EXPECTED_PERMISSIONS = ["activeTab", "scripting", "downloads", "storage", "nativeMessaging"]
EXPECTED_PRIVACY_URL = "https://gist.github.com/daynightae-cmyk/0af75547b262226946bc1b071f563a5f"
EXPECTED_ASSETS = {
    "GrabFlow-v0.6.7-English-1280x800.png": (1280, 800),
    "GrabFlow-v0.6.7-Arabic-RTL-1280x800.png": (1280, 800),
    "GrabFlow-v0.6.7-Direct-Video-1280x800.png": (1280, 800),
    "GrabFlow-v0.6.7-Promo-440x280.png": (440, 280),
    "GrabFlow-v0.6.7-Marquee-1400x560.png": (1400, 560),
    "GrabFlow-v0.6.7-Logo-300x300.png": (300, 300),
    "GrabFlow-v0.6.7-Icon-128x128.png": (128, 128),
}


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def png_dims(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def extract_text_block(document, marker):
    start = document.find(marker)
    if start < 0:
        fail(f"marker not found: {marker}")
    fence = document.find("```text", start)
    if fence < 0:
        fail(f"no text block after marker: {marker}")
    body_start = fence + len("```text")
    body_end = document.find("```", body_start)
    if body_end < 0:
        fail(f"unclosed text block after marker: {marker}")
    return document[body_start:body_end].strip()


def validate_listing(document):
    chrome_name = extract_text_block(document, "**Name (37 characters):**")
    chrome_summary = extract_text_block(document, "**Short description (129 characters):**")
    chrome_detail = extract_text_block(document, "**Detailed description:**")
    arabic_name = extract_text_block(document, "**الاسم:**")
    arabic_summary = extract_text_block(document, "**الوصف المختصر (≤132 حرفًا):**")
    arabic_detail = extract_text_block(document, "**الوصف التفصيلي:**")
    edge_summary = extract_text_block(
        document, "**Short description (from manifest, 129 characters):**"
    )
    search_terms = extract_text_block(
        document, "**Search terms (7 terms, 14 words, each ≤30 characters):**"
    ).splitlines()

    checks = [
        ("Chrome name", len(chrome_name), 1, 75),
        ("Chrome short description", len(chrome_summary), 1, 132),
        ("Chrome detailed description", len(chrome_detail), 250, 10000),
        ("Arabic name", len(arabic_name), 1, 75),
        ("Arabic short description", len(arabic_summary), 1, 132),
        ("Arabic detailed description", len(arabic_detail), 250, 10000),
        ("Edge short description", len(edge_summary), 1, 132),
        ("Edge detailed description", len(chrome_detail), 250, 10000),
    ]
    for label, length, minimum, maximum in checks:
        if not minimum <= length <= maximum:
            fail(f"{label} length {length} is outside {minimum}..{maximum}")
        print(f"LISTING_OK {label}: {length} chars (limit {minimum}..{maximum})")

    if edge_summary != chrome_summary:
        fail("Edge short description must match the manifest/Chrome summary")
    if len(search_terms) > 7:
        fail(f"too many search terms: {len(search_terms)}")
    total_words = sum(len(term.split()) for term in search_terms)
    if total_words > 21:
        fail(f"too many search-term words: {total_words}")
    for term in search_terms:
        if len(term) > 30:
            fail(f"search term exceeds 30 characters: {term!r}")
    print(f"SEARCH_TERMS_OK {len(search_terms)} terms, {total_words} words")


def validate_assets(assets_dir):
    manifest_path = assets_dir / "ASSET_SHA256.json"
    if not manifest_path.is_file():
        fail(f"missing asset manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if set(manifest) != set(EXPECTED_ASSETS):
        fail(f"asset manifest keys differ: {sorted(set(manifest) ^ set(EXPECTED_ASSETS))}")
    for name, expected_dims in EXPECTED_ASSETS.items():
        path = assets_dir / name
        if not path.is_file():
            fail(f"missing asset: {path}")
        actual_dims = png_dims(path)
        if actual_dims != expected_dims:
            fail(f"{name}: dimensions {actual_dims} != {expected_dims}")
        record = manifest[name]
        if (record["width"], record["height"]) != expected_dims:
            fail(f"{name}: manifest dimensions differ")
        if record["bytes"] != path.stat().st_size:
            fail(f"{name}: byte length differs")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if record["sha256"] != digest:
            fail(f"{name}: SHA-256 differs")
        print(f"ASSET_OK {name} {actual_dims[0]}x{actual_dims[1]} {digest[:16]}...")


def validate_manifest_and_checksums():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("version") != EXPECTED_VERSION:
        fail(f"manifest version {manifest.get('version')!r} != {EXPECTED_VERSION}")
    if manifest.get("permissions") != EXPECTED_PERMISSIONS:
        fail(f"manifest permissions differ: {manifest.get('permissions')}")
    if manifest.get("manifest_version") != 3:
        fail("manifest is not MV3")
    print("MANIFEST_OK version 0.6.7, five least-privilege permissions, MV3")

    checksum_file = ROOT / "RELEASE_CHECKSUMS-v0.6.7.sha256"
    if not checksum_file.is_file():
        fail(f"missing checksum file: {checksum_file}")
    checksums = checksum_file.read_text(encoding="utf-8")
    for package in (
        "KNOuX-GrabFlow-CHROME-v0.6.7.zip",
        "KNOuX-GrabFlow-EDGE-v0.6.7.zip",
    ):
        if not re.search(rf"^{EXPECTED_HASH}\s+{re.escape(package)}$", checksums, re.MULTILINE):
            fail(f"checksum file does not record {EXPECTED_HASH} for {package}")
    print("CHECKSUMS_OK Chrome and Edge packages match the published v0.6.7 hash")


def validate_kit_text(document):
    required = [
        "Status: PREPARED, NOT SUBMITTED, NOT APPROVED, NOT PUBLISHED.",
        "Chrome Web Store",
        "Microsoft Edge Add-ons",
        EXPECTED_PRIVACY_URL,
        EXPECTED_HASH,
        "No, I am not using remote code",
        "activeTab",
        "nativeMessaging",
        "not evidence of a Chrome Web Store or Microsoft Edge Add-ons",
        "Do not claim",
    ]
    for needle in required:
        if needle not in document:
            fail(f"kit is missing required text: {needle!r}")
    if "https://github.com/daynightae-cmyk/KNOuX-GrabFlow" in document:
        print("KIT_OK private repository is named but not presented as the public policy URL")
    print(f"KIT_OK required sections and non-claims present ({len(document)} chars)")


def confined(value, base, label):
    """Resolve a CLI-supplied path and keep it inside ``base``.

    The kit and assets directories are operator input, not trusted file paths.
    Resolving first and rejecting anything that escapes the repository root
    closes the path-traversal route before any file is opened.
    """
    resolved = Path(value).resolve()
    if not resolved.is_relative_to(base.resolve()):
        fail(f"{label} must stay inside {base}: {value}")
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assets",
        default=str(ROOT / "store-assets" / EXPECTED_VERSION),
        help="Directory containing the generated store assets.",
    )
    parser.add_argument(
        "--kit",
        default=str(ROOT / f"STORE_SUBMISSION-v{EXPECTED_VERSION}.md"),
        help="Store submission kit Markdown file.",
    )
    args = parser.parse_args()

    kit_path = confined(args.kit, ROOT, "--kit")
    assets_dir = confined(args.assets, ROOT, "--assets")
    if not kit_path.is_file():
        fail(f"missing kit: {kit_path}")
    document = kit_path.read_text(encoding="utf-8")
    validate_listing(document)
    validate_kit_text(document)
    validate_manifest_and_checksums()
    validate_assets(assets_dir)
    print("STORE_KIT_VALID")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001 - CLI must print a clear failure
        print("FAIL:", error)
        sys.exit(1)
