"""Windows-only real Chrome MV3 -> native host smoke with reversible HKCU registration.

Starts an isolated Playwright Chromium profile, registers a temporary Native
Messaging host for the generated extension ID, validates responses and removes
only the temporary registry key created by this test. Never touches a personal
Chrome profile or an existing Native Messaging host registration.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory

if sys.platform != "win32":
    raise SystemExit("BLOCKED: requires Windows, not a Windows-compatible mock")

import winreg
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HOST = "com.knoux.grabflow.companion"
REG_KEY = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST}"


def read_extension_id(context):
    page = context.new_page()
    try:
        page.goto("chrome://extensions/", wait_until="domcontentloaded")
        page.locator("extensions-item").first.wait_for(timeout=25000)
        items = page.locator("extensions-item").evaluate_all(
            "(els)=>els.map(x=>({id:x.data?.id,name:x.data?.name}))"
        )
        match = [x for x in items if "GrabFlow" in (x.get("name") or "")]
        if len(match) != 1 or len(match[0].get("id", "")) != 32:
            raise AssertionError(f"Unexpected MV3 extension list: {items}")
        return match[0]["id"]
    finally:
        page.close()


def send(page, action):
    return page.evaluate("""request => new Promise(resolve => {
        chrome.runtime.sendNativeMessage(
            'com.knoux.grabflow.companion', request, response =>
                resolve({response, error: chrome.runtime.lastError?.message || null})
        );
    })""", action)


def main():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY):
            raise RuntimeError("BLOCKED: existing Native Messaging registration belongs to user; cannot replace it")
    except FileNotFoundError:
        pass

    created = None
    with TemporaryDirectory(prefix="knoux-grabflow-native-mv3-") as dirname:
        temp = Path(dirname)
        args = [
            "--disable-extensions-except=" + str(ROOT),
            "--load-extension=" + str(ROOT),
            "--no-first-run",
        ]
        try:
            with sync_playwright() as playwright:
                ctx = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(temp / "profile"),
                    headless=True, channel="chromium", args=args
                )
                try:
                    extension_id = read_extension_id(ctx)
                finally:
                    ctx.close()

                wrapper = temp / "native_host.bat"
                wrapper.write_bytes(
                    f'@echo off\r\n"{sys.executable}" "{ROOT / "scripts" / "companion_host.py"}" %*\r\n'.encode("utf-8")
                )
                manifest = temp / "host.json"
                manifest.write_text(json.dumps({
                    "name": HOST,
                    "description": "Temporary KNOuX GrabFlow QA host",
                    "path": str(wrapper),
                    "type": "stdio",
                    "allowed_origins": [f"chrome-extension://{extension_id}/"]
                }), encoding="utf-8")
                # This key did not exist at function entry. If another agent
                # created it meanwhile, refuse to replace that user's work.
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY):
                        raise RuntimeError("BLOCKED: host registry appeared concurrently")
                except FileNotFoundError:
                    pass
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY) as reg:
                    winreg.SetValueEx(reg, "", 0, winreg.REG_SZ, str(manifest))
                created = str(manifest)

                ctx = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(temp / "profile"),
                    headless=True, channel="chromium", args=args
                )
                try:
                    assert read_extension_id(ctx) == extension_id
                    page = ctx.new_page()
                    page.goto(f"chrome-extension://{extension_id}/popup.html", wait_until="domcontentloaded")
                    pong = send(page, {"action": "ping"})
                    assert not pong["error"], f"Chrome native ping failed: {pong}"
                    assert pong["response"]["action"] == "pong", pong
                    assert pong["response"]["host"] == HOST, pong
                    expected_host_version = re.search(
                        r'^VERSION = "([^"]+)"',
                        (ROOT / "scripts" / "companion_host.py").read_text(encoding="utf-8"),
                        re.MULTILINE).group(1)
                    assert pong["response"]["version"] == expected_host_version, pong
                    # The handshake must also prove the session contract the popup
                    # now depends on, not merely that a process answered.
                    assert "assemble-async" in pong["response"]["capabilities"], pong
                    assert pong["response"]["localMediaPolicy"] == "private-addresses-blocked", pong
                    assert pong["response"]["maxConcurrentJobs"] >= 1, pong
                    import media_tools
                    ffmpeg_found = bool(media_tools.ffmpeg())
                    assert pong["response"]["ffmpegAvailable"] == ffmpeg_found, pong
                    blocked = send(page, {
                        "action": "probe",
                        "url": "http://127.0.0.1/private.m3u8",
                        "allowLocal": True
                    })
                    assert not blocked["error"], blocked
                    assert blocked["response"]["action"] == "error", blocked
                    assert "cannot be overridden" in blocked["response"]["error"], blocked
                    print(f"REAL_NATIVE_MESSAGING_PASS extension={extension_id} ffmpegAvailable={ffmpeg_found}")
                    print("REAL_BROWSER_BOUNDARY_PASS browser supplied allowLocal rejected")
                    print("LIMIT: does not assemble a full HLS/DASH stream via Chrome")
                finally:
                    ctx.close()
        finally:
            if created is not None:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY) as reg:
                        current = winreg.QueryValueEx(reg, "")[0]
                    if current != created:
                        raise RuntimeError("BLOCKED: host registry changed concurrently; preserving entry")
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_KEY)
                    print("TEMPORARY_REGISTRY_CLEANUP_PASS")
                except FileNotFoundError:
                    # If someone already removed our key, no need to recreate.
                    print("TEMPORARY_REGISTRY_ALREADY_ABSENT")
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY):
            raise AssertionError("Temporary Native Messaging key unexpectedly remains registered")
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    main()
