#!/usr/bin/env python3
"""Windows Native Companion registration utility for KNOuX GrabFlow.

Registers or unregisters the Native Messaging Host with Google Chrome
under HKCU (current user registry, no administrative privileges required).
"""

import argparse
import json
import os
import re
from pathlib import Path
import sys

HOST_NAME = "com.knoux.grabflow.companion"
SCRIPT_DIR = Path(__file__).resolve().parent


def validate_extension_id(extension_id):
    """Chrome extension IDs are exactly 32 lowercase letters a-p."""
    if not isinstance(extension_id, str) or not re.fullmatch(r'[a-p]{32}', extension_id):
        raise ValueError('Use --extension-id followed by the 32-letter ID from chrome://extensions')
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


def register(extension_id=None):
    extension_id = validate_extension_id(extension_id)
    python_exe = sys.executable
    host_py = SCRIPT_DIR / "companion_host.py"
    # Generated machine-specific files stay outside the Git source tree.
    install_dir = Path(os.environ.get('LOCALAPPDATA') or Path.home() / '.knoux') / 'KNOuX' / 'GrabFlow'
    install_dir.mkdir(parents=True, exist_ok=True)
    bat_file = install_dir / "companion_host.bat"

    # Write batch wrapper with absolute paths and CRLF
    bat_content = f"@echo off\r\n\"{python_exe}\" \"{host_py}\" %*\r\n"
    bat_file.write_text(bat_content, encoding='utf-8')

    manifest_file = install_dir / "com.knoux.grabflow.companion.json"
    manifest = build_manifest(extension_id, bat_file)
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    if sys.platform == 'win32':
        import winreg
        key_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest_file))
            print(f"SUCCESS: Registered {HOST_NAME} at HKCU\\{key_path}")
            print(f"Manifest: {manifest_file}")
            print(f"Batch Host: {bat_file}")
            return 0
        except OSError as e:
            print(f"ERROR: Could not register registry key: {e}", file=sys.stderr)
            return 1
    else:
        print(f"Non-Windows platform detected: Manifest written to {manifest_file}")
        return 0


def unregister():
    if sys.platform == 'win32':
        import winreg
        key_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            print(f"SUCCESS: Removed HKCU\\{key_path}")
        except FileNotFoundError:
            print(f"Registry key HKCU\\{key_path} not found.")
        except OSError as e:
            print(f"ERROR: Could not delete registry key: {e}", file=sys.stderr)
            return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description="Register/unregister KNOuX GrabFlow companion host.")
    parser.add_argument("--unregister", "--uninstall", action="store_true", help="Remove registration from registry")
    parser.add_argument("--extension-id", help="Chrome extension ID to allow explicitly")
    args = parser.parse_args()

    if args.unregister:
        return unregister()
    try:
        return register(args.extension_id)
    except ValueError as error:
        parser.error(str(error))


if __name__ == '__main__':
    sys.exit(main())
