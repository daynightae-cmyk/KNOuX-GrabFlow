"""Real MV3 extension + real Chrome Downloads API smoke.

Runs unpacked KNOuX GrabFlow in an isolated Playwright Chromium profile.
The discovery input in the download check is a controlled local fixture; this
does not exercise the physical toolbar-click activeTab grant or video decoding.
No Chrome API mocks are used.
"""
from functools import partial
import hashlib
import os
import shutil
import subprocess
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = Path(os.environ.get("GRABFLOW_E2E_SCREENSHOT_DIR", str(ROOT / "screenshots")))


class QuietFixtureHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run():
    with TemporaryDirectory(prefix="knoux-grabflow-real-mv3-") as tmp:
        temp_root = Path(tmp).resolve()
        downloads_dir = temp_root / "downloads"
        downloads_dir.mkdir()
        fixtures = temp_root / "media-fixtures"
        (fixtures / "icons").mkdir(parents=True)
        shutil.copy2(ROOT / "icons" / "icon128.png", fixtures / "icons" / "icon128.png")
        import media_tools
        ffmpeg, ffprobe = media_tools.pair()
        if not ffmpeg or not ffprobe:
            raise RuntimeError("BLOCKED: FFmpeg and FFprobe required for real video download integrity")
        video_fixture = fixtures / "test-video.mp4"
        subprocess.run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
            "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=12",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
            "-t", "2", "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart",
            str(video_fixture)
        ], check=True, capture_output=True, timeout=45)
        # Additional deterministic local rows used only for the populated
        # bilingual screenshots. No browser API is mocked.
        (fixtures / "stream.m3u8").write_text(
            "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:2\n"
            "#EXT-X-MEDIA-SEQUENCE:0\n#EXTINF:2.0,\nsegment0.ts\n#EXT-X-ENDLIST\n",
            encoding="utf-8",
        )
        (fixtures / "manifest.mpd").write_text(
            '<?xml version="1.0" encoding="utf-8"?>'
            '<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT2S" '
            'minBufferTime="PT1S" profiles="urn:mpeg:dash:profile:isoff-on-demand:2011">'
            '<Period><AdaptationSet mimeType="video/mp4" segmentAlignment="true">'
            '<Representation id="v0" bandwidth="128000" width="160" height="90" '
            'codecs="avc1.42E01E"><BaseURL>test-video.mp4</BaseURL>'
            '</Representation></AdaptationSet></Period></MPD>',
            encoding="utf-8",
        )
        subprocess.run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
            "-t", "1", "-c:a", "pcm_s16le", str(fixtures / "audio.wav")
        ], check=True, capture_output=True, timeout=30)
        (fixtures / "notes.txt").write_text("KNOuX GrabFlow local fixture\n", encoding="utf-8")
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            partial(QuietFixtureHandler, directory=str(fixtures)),
        )
        Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(temp_root / "profile"),
                    downloads_path=str(downloads_dir),
                    accept_downloads=True,
                    channel="chromium",
                    headless=True,
                    viewport={"width": 1280, "height": 800},
                    locale="en-US",
                    args=[
                        "--disable-extensions-except=" + str(ROOT),
                        "--load-extension=" + str(ROOT),
                        "--no-first-run",
                    ],
                )
                try:
                    extensions = context.new_page()
                    extensions.goto("chrome://extensions/", wait_until="domcontentloaded")
                    items = extensions.locator("extensions-item")
                    items.first.wait_for(timeout=20000)
                    details = items.evaluate_all("""(elements) => elements.map(el => ({
                        id: el.data?.id || el.getAttribute('id'),
                        name: el.data?.name || '',
                    }))""")
                    selected = next((item for item in details if "GrabFlow" in item["name"]), None)
                    assert selected is not None, f"GrabFlow not loaded as MV3: {details}"
                    extension_id = selected["id"]
                    assert extension_id and len(extension_id) == 32, details

                    popup = context.new_page()
                    errors = []
                    popup.on("pageerror", lambda error: errors.append(str(error)))
                    popup.goto(f"chrome-extension://{extension_id}/popup.html", wait_until="domcontentloaded")
                    popup.locator("#langBtn").wait_for(timeout=15000)
                    runtime = popup.evaluate("""() => ({
                        id: chrome.runtime.id,
                        version: chrome.runtime.getManifest().version,
                        nativeMessaging: !!chrome.runtime.sendNativeMessage,
                        scripting: !!chrome.scripting,
                        downloads: !!chrome.downloads,
                        permissions: chrome.runtime.getManifest().permissions,
                    })""")
                    expected_version = json.loads((ROOT / "manifest.json").read_text())["version"]
                    assert runtime["id"] == extension_id
                    assert runtime["version"] == expected_version, (runtime["version"], expected_version)
                    assert runtime["nativeMessaging"] and runtime["scripting"] and runtime["downloads"]
                    assert "activeTab" in runtime["permissions"]
                    assert "<all_urls>" not in runtime["permissions"]
                    popup.locator("#totalCount").wait_for(timeout=15000)
                    popup.locator("#langBtn").click()
                    assert popup.locator("html").get_attribute("dir") == "rtl"
                    popup.locator("#langBtn").click()
                    assert popup.locator("html").get_attribute("dir") == "ltr"
                    SCREENSHOTS.mkdir(parents=True, exist_ok=True)

                    # Exercise the actual extension UI and Chrome Downloads API.
                    # Only the discovery result is seeded with a deterministic
                    # local image fixture, not with fake browser APIs.
                    fixture = ROOT / "icons" / "icon128.png"
                    media_url = f"http://127.0.0.1:{server.server_port}/icons/icon128.png"
                    popup.evaluate("""url => applyScannedPage({
                        title:'Local image fixture',
                        domain:'127.0.0.1',
                        pageUrl:url,
                        assets:[{
                            type:'image',
                            url,
                            name:'icon128.png',
                            source:'local-fixture',
                        }],
                        truncated:false,
                    })""", media_url)
                    popup.locator(".asset input[type=checkbox]").first.check()
                    assert popup.locator("#downloadBtn").is_enabled()
                    popup.locator("#downloadBtn").click()

                    download_info = None
                    deadline = time.monotonic() + 20
                    while time.monotonic() < deadline:
                        records = popup.evaluate("() => chrome.downloads.search({limit:10})")
                        matches = [item for item in records if item.get("url") == media_url]
                        if matches:
                            download_info = matches[0]
                            if download_info.get("state") in ("complete", "interrupted"):
                                break
                        time.sleep(0.2)
                    assert download_info and download_info.get("state") == "complete", download_info
                    output = Path(download_info["filename"]).resolve()
                    assert output.is_relative_to(temp_root), (
                        "Isolated test attempted to save outside the test profile:", output
                    )
                    expected_bytes = fixture.read_bytes()
                    actual_bytes = output.read_bytes()
                    assert actual_bytes == expected_bytes
                    assert download_info["bytesReceived"] == len(expected_bytes)
                    checksum = hashlib.sha256(actual_bytes).hexdigest()
                    # Second independent real Chrome Downloads job: actual playable
                    # MP4 with both video and audio, generated in an isolated fixture.
                    video_url = f"http://127.0.0.1:{server.server_port}/test-video.mp4"
                    popup.evaluate("""url => applyScannedPage({
                        title: 'Local video fixture',
                        domain: '127.0.0.1',
                        pageUrl: url,
                        assets: [{
                            type: 'video',
                            url,
                            name: 'test-video.mp4',
                            source: 'local-video-fixture',
                            format: 'mp4'
                        }],
                        truncated: false
                    })""", video_url)
                    popup.locator(".asset input[type=checkbox]").first.check()
                    popup.locator("#downloadBtn").click()
                    video_record = None
                    deadline = time.monotonic() + 20
                    while time.monotonic() < deadline:
                        records = popup.evaluate("() => chrome.downloads.search({limit:20})")
                        matches = [item for item in records if item.get("url") == video_url]
                        if matches:
                            video_record = matches[0]
                            if video_record.get("state") in ("complete", "interrupted"):
                                break
                        time.sleep(0.2)
                    assert video_record and video_record.get("state") == "complete", video_record
                    saved_video = Path(video_record["filename"]).resolve()
                    assert saved_video.is_relative_to(temp_root), saved_video
                    assert saved_video.read_bytes() == video_fixture.read_bytes()
                    probe = subprocess.run([
                        ffprobe, "-v", "error",
                        "-show_entries", "format=duration:stream=codec_type",
                        "-of", "json", str(saved_video)
                    ], capture_output=True, text=True, check=True, timeout=20)
                    media_info = json.loads(probe.stdout)
                    assert {"video", "audio"}.issubset({
                        track["codec_type"] for track in media_info["streams"]
                    })
                    assert 1.7 < float(media_info["format"]["duration"]) < 2.4
                    video_digest = hashlib.sha256(saved_video.read_bytes()).hexdigest()
                    popup.screenshot(path=str(SCREENSHOTS / "real-mv3-download-complete.png"))
                    # Populated bilingual captures: deterministic local rows are
                    # seeded through the shipped applyScannedPage path; the popup,
                    # rendering, language switch and download state are real.
                    popup.evaluate("""({imageUrl, videoUrl, hlsUrl, dashUrl, audioUrl, docUrl}) => applyScannedPage({
                        title: 'KNOuX GrabFlow local fixture',
                        domain: '127.0.0.1',
                        pageUrl: hlsUrl,
                        assets: [
                            {type:'video', url:hlsUrl, name:'master.m3u8', format:'hls', source:'local-fixture'},
                            {type:'video', url:dashUrl, name:'manifest.mpd', format:'dash', source:'local-fixture'},
                            {type:'video', url:videoUrl, name:'test-video.mp4', format:'mp4', resolution:'160x90', source:'local-fixture'},
                            {type:'image', url:imageUrl, name:'icon128.png', width:128, height:128, source:'local-fixture'},
                            {type:'audio', url:audioUrl, name:'audio.wav', format:'wav', source:'local-fixture'},
                            {type:'document', url:docUrl, name:'notes.txt', source:'local-fixture'}
                        ],
                        truncated: false
                    })""", {
                        "imageUrl": media_url,
                        "videoUrl": video_url,
                        "hlsUrl": f"http://127.0.0.1:{server.server_port}/stream.m3u8",
                        "dashUrl": f"http://127.0.0.1:{server.server_port}/manifest.mpd",
                        "audioUrl": f"http://127.0.0.1:{server.server_port}/audio.wav",
                        "docUrl": f"http://127.0.0.1:{server.server_port}/notes.txt",
                    })
                    popup.wait_for_timeout(400)
                    popup.locator("#langBtn").click()
                    assert popup.locator("html").get_attribute("dir") == "rtl"
                    popup.screenshot(path=str(SCREENSHOTS / "real-mv3-ar-rtl.png"))
                    popup.locator("#langBtn").click()
                    assert popup.locator("html").get_attribute("dir") == "ltr"
                    popup.screenshot(path=str(SCREENSHOTS / "real-mv3-popup.png"))
                    assert not errors, f"Popup errors: {errors}"
                    print(f"REAL_MV3_UNPACKED_PASS: {extension_id}")
                    print(f"REAL_CHROME_DOWNLOAD_COMPLETE: {len(actual_bytes)} bytes SHA256={checksum}")
                    print(f"REAL_CHROME_MP4_COMPLETE: {saved_video.stat().st_size} bytes SHA256={video_digest} video+audio ffprobe=PASS")
                    print("VERIFIED: extension origin, no-mock browser downloads API, actual PNG+MP4 file bytes, RTL/LTR, service worker job persistence")
                    # The service worker is the reason progress survives a closed popup.
                    worker_pages = [p for p in context.service_workers]
                    sw_url = next((w.url for w in worker_pages if "background.js" in w.url), None)
                    assert sw_url, f"MV3 service worker did not register: {[w.url for w in worker_pages]}"
                    survivor = popup.evaluate("""async () => {
                        const before = await chrome.storage.local.get(['grabflowJobs']);
                        return Array.isArray(before.grabflowJobs) ? before.grabflowJobs.length : -1;
                    }""")
                    assert survivor >= 2, f"worker did not persist download jobs to storage: {survivor}"
                    print(f"SERVICE_WORKER_REGISTERED: {sw_url}")
                    print(f"WORKER_PERSISTED_JOBS: {survivor}")
                    print("NOT VERIFIED: physical toolbar action, activeTab grant, HLS/DASH assembly via native messaging")
                finally:
                    context.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    run()
