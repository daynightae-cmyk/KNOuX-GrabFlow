#!/usr/bin/env python3
"""Windows Native Companion registration utility for KNOuX GrabFlow.

Registers or unregisters the Native Messaging Host with Google Chrome
under HKCU (current user registry, no administrative privileges required).
"""

import argparse
import json
import os
from pathlib import Path
import sys

HOST_NAME = "com.knoux.grabflow.companion"
SCRIPT_DIR = Path(__file__).resolve().parent


def register(extension_id=None):
    python_exe = sys.executable
    host_py = SCRIPT_DIR / "companion_host.py"
    bat_file = SCRIPT_DIR / "companion_host.bat"

    # Write batch wrapper with absolute paths and CRLF
    bat_content = f"@echo off\r\n\"{python_exe}\" \"{host_py}\" %*\r\n"
    bat_file.write_text(bat_content, encoding='utf-8')

    manifest_file = SCRIPT_DIR / "com.knoux.grabflow.companion.json"
    allowed_origins = ["chrome-extension://*/"]
    if extension_id:
        allowed_origins.append(f"chrome-extension://{extension_id}/")

    manifest = {
        "name": HOST_NAME,
        "description": "KNOuX GrabFlow Windows Native Media Companion Host",
        "path": str(bat_file),
        "type": "stdio",
        "allowed_origins": allowed_origins
    }
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
    parser.add_argument("--unregister", action="store_true", help="Remove registration from registry")
    parser.add_argument("--extension-id", help="Chrome extension ID to allow explicitly")
    args = parser.parse_args()

    if args.unregister:
        return unregister()
    return register(args.extension_id)


if __name__ == '__main__':
    sys.exit(main())
