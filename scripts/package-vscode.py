#!/usr/bin/env python3
"""Stage and package the KNOuX GrabFlow VS Code companion as a VSIX.

Only runtime files are staged. The two Python helpers are copied from scripts/
so the installed extension never points at a repository checkout. The generated
VSIX lives under dist/ and is intentionally not committed.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "vscode-companion"
DIST = ROOT / "dist"
VERSION = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))["version"]
PACKAGE = json.loads((EXT / "package.json").read_text(encoding="utf-8"))
RUNTIME_FILES = [
    "extension.js",
    "README.md",
    "CHANGELOG.md",
    "LICENSE.txt",
    "media/icon.png",
]
HELPERS = ["assemble_stream.py", "companion_host.py"]
EXPECTED_VSIX = {
    "[Content_Types].xml",
    "extension.vsixmanifest",
    "extension/package.json",
    "extension/extension.js",
    "extension/readme.md",
    "extension/changelog.md",
    "extension/LICENSE.txt",
    "extension/media/icon.png",
    "extension/companion/assemble_stream.py",
    "extension/companion/companion_host.py",
}


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def copy_runtime(staging):
    shutil.copy2(EXT / "package.json", staging / "package.json")
    for relative in RUNTIME_FILES:
        source = EXT / relative
        target = staging / relative
        if not source.is_file() or source.is_symlink():
            fail(f"missing or unsafe runtime file: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    helper_dir = staging / "companion"
    helper_dir.mkdir(parents=True, exist_ok=True)
    for name in HELPERS:
        source = ROOT / "scripts" / name
        if not source.is_file() or source.is_symlink():
            fail(f"missing or unsafe bundled helper: {source}")
        shutil.copy2(source, helper_dir / name)

    for relative in json.loads((staging / "package.json").read_text(encoding="utf-8"))["files"]:
        if not (staging / relative).is_file():
            fail(f"package.json files entry is absent from staging: {relative}")


def check_metadata():
    if PACKAGE.get("version") != VERSION:
        fail(f"extension version {PACKAGE.get('version')!r} != browser manifest {VERSION!r}")
    if PACKAGE.get("publisher") != "knoux-labs":
        fail("unexpected publisher")
    if PACKAGE.get("license") != "SEE LICENSE IN LICENSE.txt":
        fail("license metadata must point at LICENSE.txt")
    if PACKAGE.get("icon") != "media/icon.png":
        fail("icon metadata must point at media/icon.png")
    if len(PACKAGE.get("contributes", {}).get("commands", [])) != 3:
        fail("expected exactly three contributed commands")
    expected = set(RUNTIME_FILES) | {f"companion/{name}" for name in HELPERS}
    missing = expected - set(PACKAGE.get("files", []))
    if missing:
        fail(f"package.json files is missing: {sorted(missing)}")


def package(staging, vsix):
    npx = shutil.which("npx")
    if not npx:
        fail("npx is required to run @vscode/vsce")
    command = [
        npx, "--yes", "@vscode/vsce@4.1.0", "package",
        "--no-dependencies",
        "--out", str(vsix),
    ]
    print("RUN", " ".join(command))
    result = subprocess.run(command, cwd=staging, text=True, capture_output=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    if result.returncode != 0:
        fail(f"vsce exited with {result.returncode}")
    if not vsix.is_file():
        fail(f"vsce did not create {vsix}")


def verify(vsix, staging):
    with ZipFile(vsix) as archive:
        bad = archive.testzip()
        if bad is not None:
            fail(f"VSIX CRC error: {bad}")
        names = set(archive.namelist())
        missing = EXPECTED_VSIX - names
        extra = names - EXPECTED_VSIX
        if missing:
            fail(f"VSIX is missing: {sorted(missing)}")
        if extra:
            fail(f"VSIX contains unexpected files: {sorted(extra)}")
        embedded = json.loads(archive.read("extension/package.json").decode("utf-8"))
        if embedded.get("version") != VERSION:
            fail("embedded package.json version differs")
        for name in HELPERS:
            actual = archive.read(f"extension/companion/{name}")
            expected = (ROOT / "scripts" / name).read_bytes()
            if actual != expected:
                fail(f"VSIX helper bytes differ from scripts/{name}")
        if archive.read("extension/extension.js") != (EXT / "extension.js").read_bytes():
            fail("VSIX extension.js differs from source")
    for name in sorted(EXPECTED_VSIX):
        print("VSIX_CONTENT", name)


def main():
    check_metadata()
    DIST.mkdir(exist_ok=True)
    vsix = DIST / f"KNOuX-GrabFlow-VSCODE-v{VERSION}.vsix"
    if vsix.exists():
        fail(f"refusing to overwrite an existing VSIX: {vsix}")
    with tempfile.TemporaryDirectory(prefix="knoux-vsix-stage-") as temporary:
        staging = Path(temporary)
        copy_runtime(staging)
        package(staging, vsix)
        verify(vsix, staging)
    digest = hashlib.sha256(vsix.read_bytes()).hexdigest()
    checksum = vsix.with_suffix(vsix.suffix + ".sha256")
    if checksum.exists():
        fail(f"refusing to overwrite an existing checksum: {checksum}")
    checksum.write_text(f"{digest}  {vsix.name}\n", encoding="utf-8")
    print(f"VSIX_PACKAGED {vsix} ({vsix.stat().st_size} bytes)")
    print(f"VSIX_SHA256 {digest}")
    print(f"VSIX_CHECKSUM {checksum}")


if __name__ == "__main__":
    main()
