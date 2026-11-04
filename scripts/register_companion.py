#!/usr/bin/env python3
"""Windows Native Companion registration utility for KNOuX GrabFlow.

Registers or unregisters the Native Messaging Host under HKCU (current user,
no administrative privileges required) for Google Chrome and/or Microsoft
Edge. Edge keeps its own registry hive, so a Chrome-only registration silently
leaves the companion unreachable in Edge — the Full Edition registers both.
"""

import argparse
import json
import os
import re
from pathlib import Path
import sys

HOST_NAME = "com.knoux.grabflow.companion"
SCRIPT_DIR = Path(__file__).resolve().parent

# Browser -> registry key that points at the JSON manifest file.
REGISTRY_ROOTS = {
    "chrome": rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}",
    "edge": rf"Software\Microsoft\Edge\NativeMessagingHosts\{HOST_NAME}",
}
DEFAULT_BROWSERS = ("chrome", "edge")


def validate_extension_id(extension_id):
    """Chrome/Edge unpacked extension IDs are exactly 32 lowercase letters a-p."""
    if not isinstance(extension_id, str) or not re.fullmatch(r'[a-p]{32}', extension_id):
        raise ValueError('Use --extension-id followed by the 32-letter ID from '
                         'edge://extensions or chrome://extensions')
    return extension_id


def build_manifest(extension_id, host_path):
    extension_id = validate_extension_id(extension_id)
    return {
        "name": HOST_NAME,
        "description": "KNOuX GrabFlow Windows Native Media Companion Host",
        "path": str(host_path),
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{extension_id}/"],
    }


def _write_host_files(extension_id, install_dir, extra_env=None):
    """Write the batch wrapper and JSON manifest; returns (bat, manifest) paths.

    `extra_env` is embedded as SET lines in the launcher so a portable FFmpeg
    install, or a deliberate test policy, can be recorded at registration time
    instead of depending on the caller's shell environment. These are local
    environment inputs; a browser message can never set or change them.
    """
    python_exe = sys.executable
    host_py = SCRIPT_DIR / "companion_host.py"
    # Generated machine-specific files stay outside the Git source tree.
    install_dir.mkdir(parents=True, exist_ok=True)
    bat_file = install_dir / "companion_host.bat"
    lines = ["@echo off"]
    for key, value in sorted((extra_env or {}).items()):
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key):
            raise ValueError(f'Invalid environment variable name: {key}')
        if '\r' in str(value) or '\n' in str(value):
            raise ValueError(f'Environment value for {key} must be a single line')
        lines.append(f'SET "{key}={value}"')
    lines.append(f'"{python_exe}" "{host_py}" %*')
    bat_file.write_text("\r\n".join(lines) + "\r\n", encoding='utf-8')

    manifest_file = install_dir / "com.knoux.grabflow.companion.json"
    manifest_file.write_text(json.dumps(build_manifest(extension_id, bat_file), indent=2),
                             encoding='utf-8')
    return bat_file, manifest_file


def _registry_apply(operation, keys, manifest_path=None):
    """Run a winreg operation over the selected browser keys. Returns failures."""
    import winreg
    failures = []
    for browser, key_path in keys.items():
        try:
            if operation == 'register':
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest_path))
                print(f"SUCCESS: registered {browser} at HKCU\\{key_path}")
            else:
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
                    print(f"SUCCESS: removed {browser} key HKCU\\{key_path}")
                except FileNotFoundError:
                    print(f"{browser} key HKCU\\{key_path} not found.")
        except OSError as e:
            failures.append((browser, str(e)))
            print(f"ERROR: {browser}: {e}", file=sys.stderr)
    return failures


def select_browsers(names):
    unknown = [n for n in names if n not in REGISTRY_ROOTS]
    if unknown:
        raise ValueError(f'Unknown browser target(s): {", ".join(unknown)}. '
                         f'Choose from {", ".join(REGISTRY_ROOTS)}')
    return {name: REGISTRY_ROOTS[name] for name in names}


def register(extension_id=None, browsers=DEFAULT_BROWSERS, extra_env=None):
    extension_id = validate_extension_id(extension_id)
    keys = select_browsers(browsers)
    install_dir = Path(os.environ.get('LOCALAPPDATA') or Path.home() / '.knoux') \
        / 'KNOuX' / 'GrabFlow'
    bat_file, manifest_file = _write_host_files(extension_id, install_dir, extra_env)
    print(f"Manifest: {manifest_file}")
    print(f"Batch Host: {bat_file}")
    if sys.platform != 'win32':
        print("Non-Windows platform detected: manifest written, no registry changes made.")
        return 0
    return 1 if _registry_apply('register', keys, manifest_file) else 0


def unregister(browsers=DEFAULT_BROWSERS):
    keys = select_browsers(browsers)
    if sys.platform != 'win32':
        return 0
    return 1 if _registry_apply('unregister', keys) else 0


def main():
    parser = argparse.ArgumentParser(description="Register/unregister KNOuX GrabFlow companion host.")
    parser.add_argument("--unregister", "--uninstall", action="store_true",
                        help="Remove registration from the registry")
    parser.add_argument("--extension-id", help="Chrome/Edge extension ID to allow explicitly")
    parser.add_argument("--browser", default="both",
                        choices=["chrome", "edge", "both"],
                        help="Which browser(s) to register (default: both)")
    parser.add_argument("--env", action="append", default=[], metavar="NAME=VALUE",
                        help="Record an environment variable in the generated launcher, e.g. "
                             "--env KNOUX_FFMPEG_DIR=D:\tools\ffmpeg\bin. Local input only; "
                             "a browser message cannot set or change these.")
    args = parser.parse_args()

    extra_env = {}
    for item in args.env:
        name, sep, value = item.partition('=')
        if not sep:
            parser.error(f'--env expects NAME=VALUE, got: {item}')
        extra_env[name] = value

    browsers = list(DEFAULT_BROWSERS) if args.browser == "both" else [args.browser]
    if args.unregister:
        return unregister(browsers)
    try:
        return register(args.extension_id, browsers, extra_env)
    except ValueError as error:
        parser.error(str(error))


if __name__ == '__main__':
    sys.exit(main())
