#!/usr/bin/env python3
"""Real Microsoft Edge runtime QA for KNOuX GrabFlow (Full Edition).

The v0.6.2 handoff recorded that branded Edge could not complete an
"Load unpacked" runtime test, and that Chromium-only QA was not sufficient to
call a release. This test closes that gap on the installed branded Edge:

  * the extension loads unpacked in Edge and gets a real extension origin
  * the MV3 service worker actually registers
  * the popup renders from chrome-extension:// with no page errors
  * a real file is downloaded through the extension's own UI and the saved
    bytes are compared to the source bytes
  * download state survives closing the popup — the behaviour that was
    impossible while the listener lived in the popup document
  * Arabic RTL and English LTR both apply

Nothing here mocks a browser API. If Edge is not installed the test exits with
a clear BLOCKED status rather than reporting a pass.
"""
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from tempfile import TemporaryDirectory
from threading import Thread
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = Path(os.environ.get("GRABFLOW_E2E_SCREENSHOT_DIR", str(ROOT / "screenshots")))
EXPECTED_VERSION = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))["version"]

EDGE_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import media_tools
FFMPEG, FFPROBE = media_tools.pair()


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def edge_executable():
    for candidate in EDGE_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def edge_version(path):
    for command in (
        ["powershell", "-NoProfile", "-Command",
         f"(Get-Item '{path}').VersionInfo.ProductVersion"],
        [str(path), "--version"],
    ):
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=25)
            text = (completed.stdout or completed.stderr or "").strip()
            if text:
                return text if text.lower().startswith("edge") else f"Microsoft Edge {text}"
        except (OSError, subprocess.SubprocessError):
            continue
    return "Microsoft Edge (version unreadable)"


def derive_unpacked_id(root_dir):
    """Branded Edge derives an unpacked extension ID from the UTF-16LE path.

    Chromium's usual UTF-8 derivation does not match what Edge writes, and
    edge://extensions renders nothing useful under headless, so the ID is
    computed here and confirmed against the profile store below.
    """
    digest = hashlib.sha256(str(root_dir).encode("utf-16-le")).hexdigest()
    return "".join(chr(ord("a") + int(nibble, 16)) for nibble in digest[:32])


def confirm_id_from_profile(profile_dir, root_dir):
    """Read the browser's own extension store to confirm the registered ID."""
    wanted = str(root_dir).lower().replace("/", "\\")
    for name in ("Secure Preferences", "Preferences"):
        for sub in ("Default", ""):
            path = (profile_dir / sub / name) if sub else (profile_dir / name)
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except (OSError, json.JSONDecodeError):
                continue
            settings = (data.get("extensions") or {}).get("settings") or {}
            for extension_id, record in settings.items():
                if str(record.get("path", "")).lower().replace("/", "\\") == wanted:
                    return extension_id
    return None


def run():
    edge = edge_executable()
    if not edge:
        print("BLOCKED: Microsoft Edge is not installed on this machine")
        return 2
    print(f"EDGE_BINARY: {edge}")
    print(f"EDGE_VERSION: {edge_version(edge)}")

    with TemporaryDirectory(prefix="grabflow-edge-") as tmp:
        temp_root = Path(tmp).resolve()
        downloads_dir = temp_root / "downloads"
        downloads_dir.mkdir()
        fixtures = temp_root / "fixtures"
        (fixtures / "media").mkdir(parents=True)

        png_source = fixtures / "media" / "emblem.png"
        shutil.copy2(ROOT / "icons" / "icon128.png", png_source)

        video_source = None
        if FFMPEG and Path(FFMPEG).is_file():
            video_source = fixtures / "media" / "clip.mp4"
            subprocess.run([
                FFMPEG, "-hide_banner", "-loglevel", "error", "-nostdin",
                "-f", "lavfi", "-i", "testsrc2=size=192x108:rate=12",
                "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
                "-t", "2", "-c:v", "libx264", "-preset", "ultrafast",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart",
                str(video_source)], check=True, capture_output=True, timeout=90)
            print(f"VIDEO_FIXTURE: real MP4 {video_source.stat().st_size} bytes")
        else:
            print("VIDEO_FIXTURE: SKIPPED (no FFmpeg; byte-verified video download not claimed)")

        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(fixtures)))
        Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_port

        # A real page with real markup: the scanner runs against it through the
        # extension's own scripting path, not through a seeded fixture.
        (fixtures / "page.html").write_text(
            "<!doctype html><html><head><title>KNOuX Edge QA Fixture</title>"
            '<link rel="preload" as="video" href="/media/clip.mp4">'
            "</head><body>"
            '<img src="/media/emblem.png" alt="Emblem fixture" width="128" height="128">'
            '<video src="/media/clip.mp4" controls width="192" height="108"></video>'
            '<a href="/media/emblem.png">Download emblem</a>'
            '<a href="/media/stream.m3u8">Stream</a>'
            "</body></html>", encoding="utf-8")

        headless = os.environ.get("GRABFLOW_EDGE_HEADLESS", "1") != "0"
        print(f"EDGE_LAUNCH_MODE: {'headless=new' if headless else 'headed'}")

        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(temp_root / "profile"),
                downloads_path=str(downloads_dir),
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
            failures = []
            try:
                # ---- 1. the extension really loaded in Edge -----------------
                # edge://extensions renders no usable DOM under headless Edge, so
                # the ID is derived from the path and then confirmed against the
                # profile's own extension store and a live runtime round-trip.
                profile_dir = temp_root / "profile"
                time.sleep(2.5)
                derived = derive_unpacked_id(ROOT)
                confirmed = confirm_id_from_profile(profile_dir, ROOT)
                extension_id = confirmed or derived
                assert extension_id and len(extension_id) == 32, extension_id
                print(f"[1] EDGE_UNPACKED_REGISTERED derived={derived} "
                      f"profile_confirmed={confirmed} "
                      f"match={'yes' if confirmed == derived else 'using profile value'}")

                probe = context.new_page()
                probe.goto(f"chrome-extension://{extension_id}/popup.html",
                           wait_until="domcontentloaded", timeout=30000)
                live_id = probe.evaluate("() => chrome.runtime.id")
                assert live_id == extension_id, (live_id, extension_id)
                print(f"    EDGE_EXTENSION_ORIGIN_LIVE chrome-extension://{live_id}")
                probe.close()

                # ---- 2. the MV3 service worker is answering ------------------
                # Playwright does not surface Edge's headless service-worker event,
                # so the worker is proven by a message round-trip it alone can serve.
                popup = context.new_page()
                page_errors = []
                popup.on("pageerror", lambda error: page_errors.append(str(error)))
                popup.goto(f"chrome-extension://{extension_id}/popup.html",
                           wait_until="domcontentloaded")
                popup.locator("#langBtn").wait_for(timeout=20000)
                worker_reply = popup.evaluate("""async () => {
                    const reply = await chrome.runtime.sendMessage({type: 'jobs:list'});
                    const manifest = chrome.runtime.getManifest();
                    return {reply, hasJobsList: !!(reply && Array.isArray(reply.jobs)),
                            workerReady: state.workerReady,
                            sw: manifest.background && manifest.background.service_worker};
                }""")
                assert worker_reply["sw"] == "background.js", worker_reply
                assert worker_reply["hasJobsList"], (
                    f"service worker did not answer jobs:list: {worker_reply}")
                assert worker_reply["workerReady"] is True, worker_reply
                print(f"[2] EDGE_SERVICE_WORKER_ALIVE answered jobs:list "
                      f"jobs={len(worker_reply['reply']['jobs'])} popupBridge=True")

                # ---- 3. popup renders from the extension origin -------------
                manifest_runtime = popup.evaluate("""async () => {
                    const m = chrome.runtime.getManifest();
                    return {version: m.version, name: chrome.i18n.getMessage('appName'),
                            description: chrome.i18n.getMessage('appDesc'),
                            permissions: m.permissions, background: m.background,
                            buildTag: document.getElementById('buildTag').textContent};
                }""")
                assert manifest_runtime["version"] == EXPECTED_VERSION, manifest_runtime
                assert manifest_runtime["name"], "i18n appName did not resolve in Edge"
                assert manifest_runtime["description"], "i18n appDesc did not resolve in Edge"
                assert manifest_runtime["background"] == {"service_worker": "background.js"}
                assert "<all_urls>" not in manifest_runtime["permissions"]
                assert EXPECTED_VERSION in manifest_runtime["buildTag"], manifest_runtime
                print(f"[3] EDGE_POPUP_RENDERED name='{manifest_runtime['name']}' "
                      f"badge='{manifest_runtime['buildTag']}' "
                      f"permissions={manifest_runtime['permissions']}")

                # ---- 4. real discovery against real page markup --------------
                # Pressing the toolbar button is what grants activeTab, and
                # automation cannot press it. The shipped scanner still runs for
                # real either way: through the extension's scripting path when the
                # grant exists, otherwise by executing the identical injected
                # function inside the page. Neither route is a canned fixture list.
                page = context.new_page()
                page.goto(f"http://127.0.0.1:{port}/page.html", wait_until="load")
                page.wait_for_timeout(1200)
                popup.bring_to_front()
                popup.evaluate("() => scan()")
                popup.wait_for_timeout(2500)
                scan_route = popup.evaluate("""() => ({
                    route: state.assets.length ? 'extension-scripting' : 'blocked',
                    error: document.getElementById('notice').textContent || null})""")
                if scan_route["route"] != "extension-scripting":
                    print(f"    activeTab grant unavailable under automation "
                          f"({scan_route['error']}); running the shipped scanner in-page")
                    scanner_source = (ROOT / "scan-page.js").read_text(encoding="utf-8")
                    in_page = page.evaluate(scanner_source + "\nscanPageAssets()")
                    popup.evaluate("result => applyScannedPage(result)", in_page)
                    popup.wait_for_timeout(800)
                    discovered = popup.evaluate("""() => ({
                        route: 'in-page-shipped-scanner',
                        host: document.getElementById('pageHost').textContent,
                        total: document.getElementById('totalCount').textContent,
                        assets: state.assets.map(a => ({type:a.type, format:a.format||null,
                                                        source:a.source, url:a.url, name:a.name,
                                                        width:a.width||0, height:a.height||0,
                                                        poster:a.poster||null}))})""")
                else:
                    discovered = popup.evaluate("""() => ({
                        route: 'extension-scripting',
                        host: document.getElementById('pageHost').textContent,
                        total: document.getElementById('totalCount').textContent,
                        assets: state.assets.map(a => ({type:a.type, format:a.format||null,
                                                        source:a.source, url:a.url, name:a.name,
                                                        width:a.width||0, height:a.height||0,
                                                        poster:a.poster||null}))})""")
                urls = {a["url"] for a in discovered["assets"]}
                assert any(u.endswith("emblem.png") for u in urls), discovered
                assert any(u.endswith("clip.mp4") for u in urls), discovered
                assert any(u.endswith("stream.m3u8") for u in urls), discovered
                m3u8 = next(a for a in discovered["assets"] if a["url"].endswith("stream.m3u8"))
                assert m3u8["format"] == "hls", m3u8
                print(f"[4] EDGE_REAL_SCAN route={discovered['route']} total={discovered['total']} "
                      f"sources={sorted({a['source'] for a in discovered['assets']})}")
                for asset in discovered["assets"]:
                    print(f"      {asset['type']:8} {str(asset['format']):8} {asset['source']:16} {asset['url']}")


                # ---- 5. bilingual ------------------------------------------------
                popup.locator("#langBtn").click()
                assert popup.locator("html").get_attribute("dir") == "rtl"
                SCREENSHOTS.mkdir(parents=True, exist_ok=True)
                popup.screenshot(path=str(SCREENSHOTS / "edge-rtl.png"), full_page=False)
                popup.locator("#langBtn").click()
                assert popup.locator("html").get_attribute("dir") == "ltr"
                assert popup.evaluate("() => document.getElementById('totalCount').textContent") != "00"
                print("[5] EDGE_BILINGUAL_RTL_LTR OK")

                # ---- 6. real download of a genuinely discovered asset --------
                # Nothing is seeded here: the URL comes from step 4's scan of the
                # real fixture markup, so this is discovery -> selection -> bytes.
                png_url = next(a["url"] for a in discovered["assets"]
                               if a["url"].endswith("emblem.png"))
                popup.evaluate("""() => {
                    state.filter = 'all';
                    document.getElementById('search').value = 'emblem';
                    render();
                }""")
                popup.locator(".asset input[type=checkbox]").first.check()
                assert popup.locator("#downloadBtn").is_enabled()
                popup.locator("#downloadBtn").click()

                record = None
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    records = popup.evaluate("() => chrome.downloads.search({limit: 10})")
                    match = [r for r in records if r.get("url") == png_url]
                    if match:
                        record = match[0]
                        if record.get("state") in ("complete", "interrupted"):
                            break
                    time.sleep(0.25)
                assert record and record.get("state") == "complete", record
                saved = Path(record["filename"]).resolve()
                assert saved.is_relative_to(temp_root), f"saved outside the sandbox: {saved}"
                expected_bytes = png_source.read_bytes()
                actual_bytes = saved.read_bytes()
                assert actual_bytes == expected_bytes, "downloaded bytes differ from source"
                assert record["bytesReceived"] == len(expected_bytes)
                sha = hashlib.sha256(actual_bytes).hexdigest()
                print(f"[6] EDGE_REAL_DOWNLOAD discovered={png_url}")
                print(f"    EDGE_DOWNLOAD_BYTES_VERIFIED {len(actual_bytes)} bytes "
                      f"SHA256={sha} saved={saved.relative_to(temp_root)}")
                # Playwright's download interception assigns the final file name, so
                # the namespaced path is verified where the extension controls it:
                # the job record the worker keeps for the Download Manager.
                job = None
                enrich_deadline = time.monotonic() + 15
                while time.monotonic() < enrich_deadline:
                    job = popup.evaluate(
                        "url => [...state.jobs.values()].find(j => j.url === url) || null", png_url)
                    if job and job.get("fileSize"):
                        break
                    time.sleep(0.4)
                assert job and job.get("kind") == "chrome", job
                assert job.get("state") == "complete", job
                assert job.get("fileSize") == len(expected_bytes), job
                print(f"    EDGE_WORKER_JOB_TRACKED kind={job['kind']} state={job['state']} "
                      f"size={job['fileSize']} finalName={Path(job['filename']).name}")

                # ---- 7. the headline fix: progress survives closing the popup --
                popup.close()
                time.sleep(2.0)          # the popup document is gone entirely
                reopened = context.new_page()
                reopened.goto(f"chrome-extension://{extension_id}/popup.html",
                              wait_until="domcontentloaded")
                reopened.locator("#managerToggleBtn").wait_for(timeout=20000)
                reopened.locator("#managerToggleBtn").click()
                reopened.wait_for_timeout(1500)
                persisted = reopened.evaluate("""async () => {
                    const stored = await chrome.storage.local.get(['grabflowJobs']);
                    const jobs = Array.isArray(stored.grabflowJobs) ? stored.grabflowJobs : [];
                    return {count: jobs.length,
                            complete: jobs.filter(j => j.state === 'complete').length,
                            cards: document.querySelectorAll('.dl-card').length,
                            names: [...document.querySelectorAll('.dl-card-name')].map(n => n.textContent)};
                }""")
                assert persisted["count"] >= 1, f"worker did not persist jobs: {persisted}"
                assert persisted["complete"] >= 1, f"job did not reach complete: {persisted}"
                assert persisted["cards"] >= 1, f"manager rendered no cards: {persisted}"
                print(f"[7] EDGE_PROGRESS_SURVIVES_POPUP_CLOSE jobs={persisted['count']} "
                      f"complete={persisted['complete']} cards={persisted['cards']} "
                      f"names={persisted['names']}")
                reopened.screenshot(path=str(SCREENSHOTS / "edge-download-manager.png"))

                # ---- 8. companion status must be truthful, never decorative ----
                pill = reopened.evaluate("() => document.getElementById('companionStatus').textContent")
                assert pill and "CHECKING" not in pill.upper(), f"companion pill stuck: {pill}"
                pill_state = reopened.evaluate("""() => ({
                    connected: state.companion.connected,
                    missingTools: state.companion.missingTools,
                    error: state.companion.error || null,
                    version: state.companion.version})""")
                print(f"[8] EDGE_COMPANION_TRUTHFUL pill='{pill}' state={pill_state}")
                if not pill_state["connected"]:
                    print("      (companion not registered on this machine — UI says so; "
                          "no assembly capability is claimed)")

                # ---- 9. optional real MP4 download + integrity --------------
                if video_source:
                    video_url = next(a["url"] for a in discovered["assets"]
                                     if a["url"].endswith("clip.mp4"))
                    # Re-apply the same real scan output into the reopened session.
                    reopened.evaluate("result => applyScannedPage(result)", {
                        "title": "KNOuX Edge QA Fixture", "domain": "127.0.0.1",
                        "pageUrl": f"http://127.0.0.1:{port}/page.html",
                        "assets": discovered["assets"], "truncated": False})
                    # Step 7 left the popup in Download Manager view; discovery rows
                    # live in the scanner panel, which is genuinely hidden now.
                    reopened.evaluate("""() => {
                        if (document.getElementById('scannerView').hidden) {
                            document.getElementById('managerToggleBtn').click();
                        }
                    }""")
                    reopened.evaluate("""() => {
                        state.filter = 'video';
                        document.getElementById('search').value = 'clip';
                        render();
                    }""")
                    reopened.wait_for_timeout(400)
                    reopened.locator(".asset input[type=checkbox]").first.check()
                    reopened.locator("#downloadBtn").click()
                    video_record = None
                    deadline = time.monotonic() + 30
                    while time.monotonic() < deadline:
                        records = reopened.evaluate("() => chrome.downloads.search({limit: 20})")
                        match = [r for r in records if r.get("url") == video_url]
                        if match:
                            video_record = match[0]
                            if video_record.get("state") in ("complete", "interrupted"):
                                break
                        time.sleep(0.25)
                    assert video_record and video_record["state"] == "complete", video_record
                    saved_video = Path(video_record["filename"]).resolve()
                    assert saved_video.read_bytes() == video_source.read_bytes()
                    if FFPROBE and Path(FFPROBE).is_file():
                        probe = json.loads(subprocess.run(
                            [FFPROBE, "-v", "error", "-show_entries",
                             "format=duration:stream=codec_type", "-of", "json",
                             str(saved_video)], capture_output=True, text=True,
                            check=True, timeout=30).stdout)
                        kinds = {s["codec_type"] for s in probe["streams"]}
                        assert {"video", "audio"} <= kinds, probe
                        print(f"[9] EDGE_MP4_INTEGRITY {saved_video.stat().st_size} bytes "
                              f"duration={probe['format']['duration']} tracks={sorted(kinds)}")
                    else:
                        print("[9] EDGE_MP4_BYTES_VERIFIED (ffprobe absent; codec claim skipped)")

                reopened.screenshot(path=str(SCREENSHOTS / "edge-popup.png"))
                assert not page_errors, f"popup page errors: {page_errors}"
                print("\nEDGE_RUNTIME_PASS "
                      f"edge={edge_version(edge)} extension={extension_id} v{EXPECTED_VERSION}")
                print("VERIFIED: branded Edge load-unpacked, service worker registration, "
                      "extension-origin popup, on-demand DOM scan of a real page, "
                      "byte-identical real downloads, job state across popup close, RTL/LTR, "
                      "truthful companion status")
                print("NOT VERIFIED here: physical toolbar click, native messaging handshake "
                      "(see tests/test-real-native-messaging-win.py and "
                      "tests/test-companion-protocol.py)")
            except AssertionError as exc:
                failures.append(str(exc))
                try:
                    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
                    context.new_page().screenshot(path=str(SCREENSHOTS / "edge-failure.png"))
                except Exception:
                    pass
                print("\nEDGE_RUNTIME_FAIL: " + str(exc))
            finally:
                context.close()
            if failures:
                return 1
            return 0


if __name__ == "__main__":
    sys.exit(run())
