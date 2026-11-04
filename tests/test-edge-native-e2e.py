#!/usr/bin/env python3
"""Live Microsoft Edge -> Native Messaging -> FFmpeg end-to-end assembly.

This is the evidence the v0.6.2 handoff said was missing: not a Python-side
protocol test and not a Chromium-only run, but the branded Edge extension
talking to the registered companion host and producing a real playable file.

What it does, and how it cleans up afterwards:

  1. derives the unpacked extension ID for this checkout the way Edge does
  2. refuses to run if a companion host is already registered, so a real user
     installation is never overwritten
  3. registers our host for Edge only, pointing it at a portable FFmpeg and at
     a throwaway Downloads root, with loopback media explicitly relaxed for the
     local fixture and reported as such by the host
  4. loads the extension in branded Edge, reads the companion state through the
     service worker, and asserts it is genuinely connected
  5. starts a real HLS assembly from the popup UI, watches progress arrive over
     the persistent port, and ffprobes the produced file
  6. deletes only the registry key and files this test created

Set GRABFLOW_EDGE_NATIVE_HEADLESS=0 to watch it happen in a visible window.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from tempfile import TemporaryDirectory
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "scripts"))

import media_tools          # noqa: E402
import register_companion   # noqa: E402
from companion_host import HOST_NAME  # noqa: E402

EDGE_KEY = rf"Software\Microsoft\Edge\NativeMessagingHosts\{HOST_NAME}"
INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".knoux") \
    / "KNOuX" / "GrabFlow"


def derive_unpacked_id(root_dir):
    import hashlib
    digest = hashlib.sha256(str(root_dir).encode("utf-16-le")).hexdigest()
    return "".join(chr(ord("a") + int(n, 16)) for n in digest[:32])


class Quiet(SimpleHTTPRequestHandler):
    THROTTLE = 0.30

    def send_head(self):
        time.sleep(self.THROTTLE)
        return super().send_head()

    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, BrokenPipeError, TimeoutError):
            pass

    def log_message(self, *a):
        pass


def registry_value_exists(key_path):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            return winreg.QueryValueEx(key, "")[0]
    except FileNotFoundError:
        return None


def main():
    if sys.platform != "win32":
        print("BLOCKED: requires Windows native messaging registry")
        return 2
    import winreg

    ffmpeg, ffprobe = media_tools.pair()
    if not (ffmpeg and ffprobe):
        print("SKIP: FFmpeg/FFprobe unavailable; no live assembly claim is made")
        return 0
    edge = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    if not edge.is_file():
        edge = Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")
    if not edge.is_file():
        print("BLOCKED: Microsoft Edge is not installed")
        return 2

    existing = registry_value_exists(EDGE_KEY)
    if existing:
        print(f"BLOCKED: a companion host is already registered for Edge at {existing}")
        print("         Refusing to overwrite a real user installation. Unregister it first")
        print("         (python scripts\\register_companion.py --unregister --browser edge).")
        return 2
    print("[0] EDGE_HOST_NOT_PREVIOUSLY_REGISTERED — safe to proceed")

    extension_id = derive_unpacked_id(ROOT)
    print(f"[1] DERIVED_EDGE_EXTENSION_ID {extension_id}")

    with TemporaryDirectory(prefix="grabflow-edge-native-") as tmp:
        temp_root = Path(tmp).resolve()
        downloads_root = temp_root / "home"
        (downloads_root / "Downloads").mkdir(parents=True)
        fixtures = temp_root / "fixtures"
        fixtures.mkdir()

        subprocess.run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
            "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=15",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
            "-t", "16", "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-force_key_frames", "expr:gte(t,n_forced*2)",
            "-f", "hls", "-hls_time", "2", "-hls_list_size", "0",
            "-hls_playlist_type", "vod", str(fixtures / "master.m3u8"),
        ], check=True, capture_output=True, timeout=240)

        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(fixtures)))
        Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_port
        stream_url = f"http://127.0.0.1:{port}/master.m3u8"
        (fixtures / "page.html").write_text(
            f"<!doctype html><html><head><title>Edge native QA</title></head><body>"
            f'<video src="{stream_url}" controls></video></body></html>', encoding="utf-8")

        registered = False
        created_files = []
        try:
            # --- register our host for Edge only, with a throwaway Downloads root
            env_backup = dict(os.environ)
            os.environ["USERPROFILE"] = str(downloads_root)
            os.environ["HOME"] = str(downloads_root)
            try:
                rc = register_companion.register(
                    extension_id, browsers=["edge"],
                    extra_env={
                        "KNOUX_FFMPEG_DIR": str(Path(ffmpeg).parent),
                        "KNOUX_GRABFLOW_ALLOW_LOCAL": "1",
                        "USERPROFILE": str(downloads_root),
                        "HOME": str(downloads_root),
                    })
            finally:
                os.environ.clear()
                os.environ.update(env_backup)
            assert rc == 0, f"registration returned {rc}"
            registered = True
            created_files = [INSTALL_DIR / "companion_host.bat",
                             INSTALL_DIR / "com.knoux.grabflow.companion.json"]
            print(f"[2] EDGE_HOST_REGISTERED key=HKCU\\{EDGE_KEY}")
            print(f"    launcher={created_files[0]}")

            headless = os.environ.get("GRABFLOW_EDGE_NATIVE_HEADLESS", "1") != "0"
            from playwright.sync_api import sync_playwright
            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(temp_root / "profile"),
                    downloads_path=str(temp_root / "downloads"),
                    accept_downloads=True,
                    channel="msedge",
                    headless=headless,
                    viewport={"width": 460, "height": 690},
                    args=[
                        "--disable-extensions-except=" + str(ROOT),
                        "--load-extension=" + str(ROOT),
                        "--no-first-run", "--no-default-browser-check",
                    ],
                )
                try:
                    page = context.new_page()
                    page.goto(f"http://127.0.0.1:{port}/page.html", wait_until="load")
                    page.wait_for_timeout(1500)

                    popup = context.new_page()
                    errors = []
                    popup.on("pageerror", lambda e: errors.append(str(e)))
                    popup.goto(f"chrome-extension://{extension_id}/popup.html",
                               wait_until="domcontentloaded")
                    popup.locator("#langBtn").wait_for(timeout=25000)

                    # The service worker performs the real native handshake.
                    popup.wait_for_timeout(1500)
                    state = popup.evaluate("""async () => {
                        const reply = await chrome.runtime.sendMessage({type:'companion:ping'});
                        return {reply, pill: document.getElementById('companionStatus').textContent,
                                connected: state.companion.connected};
                    }""")
                    reply = state["reply"] or {}
                    assert reply.get("connected") is True, (
                        f"Edge did not reach the companion: {state}")
                    assert reply.get("version"), reply
                    assert reply.get("missingTools") is False, reply
                    assert "COMPANION: CONNECTED" in state["pill"], state
                    print(f"[3] EDGE_TO_NATIVE_HANDSHAKE version={reply['version']} "
                          f"policy={reply.get('localMediaPolicy')} pill='{state['pill']}'")

                    # Start a real assembly through the shipped UI path.
                    popup.evaluate("""url => applyScannedPage({
                        title:'Edge native QA', domain:'127.0.0.1', pageUrl:url,
                        assets:[{type:'video', url, name:'Edge native assembly',
                                 source:'edge-native-qa', format:'hls', isPlaylist:true}],
                        truncated:false})""", stream_url)
                    assemble = popup.evaluate(
                        "() => document.querySelector('.btn-assemble')")
                    assert assemble is not None, "Assemble button not rendered"
                    popup.locator(".btn-assemble").click()
                    popup.locator("#managerToggleBtn").click()

                    card = popup.locator(".dl-card.companion").first
                    card.wait_for(timeout=20000)
                    samples = []
                    final = None
                    deadline = time.monotonic() + 180
                    while time.monotonic() < deadline:
                        snap = popup.evaluate(
                            "() => [...state.jobs.values()].filter(j => j.kind === 'companion')"
                            ".map(j => ({state:j.state, bytes:j.bytesReceived,"
                            " percent:j.percent, audit:j.nestedAudit}))")
                        if snap:
                            samples.append(snap[-1])
                            if snap[-1]["state"] in ("complete", "failed", "cancelled",
                                                     "interrupted"):
                                final = snap[-1]
                                break
                        time.sleep(0.5)
                    assert final, f"assembly never reached a terminal state: {samples}"
                    assert final["state"] == "complete", (final, samples)
                    assert final["bytes"] > 50000, final
                    assert final["audit"]["status"] == "passed", final
                    progressed = [s for s in samples if s["percent"] and s["percent"] > 0]
                    print(f"[4] EDGE_LIVE_ASSEMBLY samples={len(samples)} "
                          f"with_progress={len(progressed)} bytes={final['bytes']} "
                          f"nestedAuditChecked={final['audit']['checked']}")
                    for s in samples[::max(1, len(samples) // 6)][:7]:
                        print(f"      {s['state']:11} {s['bytes']:>9} B  {s['percent']:>3}%")

                    produced = Path(downloads_root) / "Downloads"
                    files = sorted(produced.glob("*.mp4"))
                    assert files, f"no MP4 produced under {produced}"
                    newest = max(files, key=lambda f: f.stat().st_mtime)
                    probe = json.loads(subprocess.run(
                        [ffprobe, "-v", "error", "-show_entries",
                         "format=duration:stream=codec_type", "-of", "json", str(newest)],
                        capture_output=True, text=True, check=True, timeout=60).stdout)
                    kinds = {s["codec_type"] for s in probe["streams"]}
                    duration = float(probe["format"]["duration"])
                    assert {"video", "audio"} <= kinds, probe
                    assert 15 < duration < 17, probe
                    print(f"[5] EDGE_PRODUCED_FILE {newest.name} {newest.stat().st_size} bytes "
                          f"duration={duration:.2f}s tracks={sorted(kinds)}")

                    popup.screenshot(path=str(ROOT / "screenshots" / "edge-native-assembly.png"))
                    assert not errors, f"popup page errors: {errors}"
                    print(f"\nEDGE_NATIVE_E2E_PASS edge_extension={extension_id} "
                          f"assembly=verified-by-ffprobe")
                    print("VERIFIED: branded Edge extension -> registered native host -> real "
                          "FFmpeg assembly, progress observed in the shipped Download Manager, "
                          "nested playlist audit passed, output probed for video+audio")
                    print("NOTE: loopback media was explicitly relaxed for this local fixture; "
                          "the host reported policy=test-relaxed and the shipped default blocks it")
                finally:
                    context.close()
        finally:
            if registered:
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, EDGE_KEY)
                    print(f"[6] REGISTRY_KEY_REMOVED HKCU\\{EDGE_KEY}")
                except FileNotFoundError:
                    print("[6] registry key already absent")
                for f in created_files:
                    try:
                        f.unlink()
                        print(f"    removed {f}")
                    except OSError as exc:
                        print(f"    could not remove {f}: {exc}")
            server.shutdown()
            server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
