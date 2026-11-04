#!/usr/bin/env python3
"""Real native-messaging protocol test for the hardened companion.

Speaks the actual length-prefixed native-messaging protocol against
scripts/companion_host.py as a subprocess, exactly as Chrome/Edge would, and
requires the result to be a genuinely playable file produced by real FFmpeg.

Evidence produced: async progress frames with byte counts, a byte-verified
MP4 probed by real ffprobe, a mid-flight cancellation, strict SSRF/scheme/
credential/playlist refusals, browser policy-override refusal, and nested
playlist references audited against a mocked DNS rebinding answer.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import queue
import shutil
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import media_tools
FFMPEG, FFPROBE = media_tools.pair()
PYTHON = sys.executable

if not (Path(FFMPEG).is_file() and Path(FFPROBE).is_file()):
    print("SKIP: FFmpeg/FFprobe missing; no real stream assembly claim")
    sys.exit(0)


def frame(obj):
    data = json.dumps(obj).encode("utf-8")
    return struct.pack("<I", len(data)) + data


def read_frame(stream):
    head = stream.read(4)
    if len(head) < 4:
        return None
    payload = stream.read(struct.unpack("<I", head)[0])
    return json.loads(payload.decode("utf-8"))


class FrameReader:
    """Native-messaging reader with a per-wait deadline so nothing can hang."""

    def __init__(self, stream, label):
        self.stream = stream
        self.label = label
        self.queue = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        while True:
            try:
                msg = read_frame(self.stream)
            except Exception as exc:  # noqa: BLE001
                self.queue.put({"action": "_reader_error", "error": str(exc)})
                return
            if msg is None:
                self.queue.put({"action": "_eof"})
                return
            self.queue.put(msg)

    def wait_for(self, predicate, timeout, label=None):
        target = label or self.label
        deadline = time.time() + timeout
        seen = []
        while time.time() < deadline:
            try:
                msg = self.queue.get(timeout=max(0.05, deadline - time.time()))
            except queue.Empty:
                break
            print(f"   << {msg.get('action')}: {json.dumps(msg, default=str)[:160]}")
            if predicate(msg):
                return msg, seen
            seen.append(msg)
            if msg.get("action") in ("_eof", "_reader_error", "error"):
                raise AssertionError(f"host ended while waiting for {target}: {msg}")
        raise AssertionError(f"timed out waiting for {target} (stderr tail: "
                             f"{getattr(self, 'stderr', '')})")


class Quiet(SimpleHTTPRequestHandler):
    # A deliberately slow origin: without it a 24-second clip muxes in well
    # under a second and progress/cancel could never be observed mid-flight.
    THROTTLE = 0.35

    def send_head(self):
        time.sleep(self.THROTTLE)
        return super().send_head()

    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, BrokenPipeError, TimeoutError):
            pass   # a cancelled assembly closes the connection; that is expected

    def log_message(self, *a):
        pass


def spawn_host(env, label):
    proc = subprocess.Popen(
        [PYTHON, str(ROOT / "scripts" / "companion_host.py")],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, env=env,
    )
    err_lines = []

    def drain():
        for line in proc.stderr:
            err_lines.append(line.decode("utf-8", "replace").rstrip())

    threading.Thread(target=drain, daemon=True).start()
    reader = FrameReader(proc.stdout, label)
    reader.stderr = err_lines
    return proc, reader, err_lines


def send(proc, payload):
    proc.stdin.write(frame(payload))
    proc.stdin.flush()


def main():
    with TemporaryDirectory(prefix="grabflow-proto-") as tmp:
        root = Path(tmp)
        fixtures = root / "fixtures"
        fixtures.mkdir()
        out_dir = root / "out" / "Downloads"
        out_dir.mkdir(parents=True)

        subprocess.run([
            FFMPEG, "-hide_banner", "-loglevel", "error", "-nostdin",
            "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=15",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
            "-t", "24", "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-force_key_frames", "expr:gte(t,n_forced*2)",
            "-f", "hls", "-hls_time", "2", "-hls_list_size", "0",
            "-hls_playlist_type", "vod", str(fixtures / "master.m3u8"),
        ], check=True, capture_output=True, timeout=180)
        (fixtures / "evil.m3u8").write_text(
            "#EXTM3U\n#EXT-X-VERSION:3\n#EXTINF:2.0,\n"
            "http://127.0.0.1:9/secret.ts\n#EXT-X-ENDLIST\n", encoding="utf-8")

        server = ThreadingHTTPServer(("127.0.0.1", 0),
                                     partial(Quiet, directory=str(fixtures)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_port
        url = f"http://127.0.0.1:{port}/master.m3u8"

        base_env = dict(os.environ)
        base_env["HOME"] = str(out_dir.parent)
        base_env["USERPROFILE"] = str(out_dir.parent)
        if os.environ.get("KNOUX_FFMPEG_DIR"):
            base_env["KNOUX_FFMPEG_DIR"] = os.environ["KNOUX_FFMPEG_DIR"]

        try:
            # ---------- Relaxed policy host: real assembly, progress, cancel ----
            relaxed = dict(base_env, KNOUX_GRABFLOW_ALLOW_LOCAL="1")
            host, reader, err = spawn_host(relaxed, "relaxed")
            try:
                send(host, {"action": "ping", "requestId": "p1"})
                pong, _ = reader.wait_for(lambda m: m.get("action") == "pong", 20, "pong")
                assert pong["requestId"] == "p1"
                assert pong["version"] == "0.6.3", pong["version"]
                assert "assemble-async" in pong["capabilities"]
                assert pong["ffmpegAvailable"] and pong["ffprobeAvailable"], pong
                print(f"[1] PING OK  version={pong['version']} policy={pong['localMediaPolicy']} "
                      f"caps={pong['capabilities']}")

                send(host, {"action": "probe", "url": url, "requestId": "q1"})
                res, _ = reader.wait_for(lambda m: m.get("action") == "probe_result", 40, "probe")
                assert res["status"] == "ok", res
                assert 23 < res["durationSeconds"] < 25, res
                assert res["videoTracks"] and res["audioTracks"], res
                assert res["drmSuspected"] is False, res
                print(f"[2] PROBE OK duration={res['durationSeconds']}s "
                      f"video={res['videoTracks'][0]} audio={res['audioTracks'][0]}")

                send(host, {"action": "assemble", "url": url, "output": "proto.mp4",
                            "jobId": "j1", "async": True})
                started, _ = reader.wait_for(lambda m: m.get("action") == "assemble_started",
                                             20, "assemble_started")
                print(f"[3] ASSEMBLE STARTED nestedAudit={started.get('nestedAudit')}")

                final, seen = reader.wait_for(
                    lambda m: m.get("action") == "assemble_result" and m.get("jobId") == "j1",
                    180, "assemble_result j1")
                progress = [m for m in seen if m.get("action") == "assemble_progress"]
                assert final["status"] == "complete", final
                produced = Path(final["output"])
                assert produced.is_file() and produced.stat().st_size > 10000, final
                assert final["bytes"] == produced.stat().st_size, final
                print(f"[4] PROGRESS FRAMES={len(progress)} "
                      f"last={progress[-1] if progress else 'none'}")
                print(f"[5] ASSEMBLE COMPLETE bytes={final['bytes']} "
                      f"percent={final['percent']} elapsed={final['elapsedSeconds']}s")
                assert len(progress) >= 2, "async assembly must stream multiple progress frames"

                media = json.loads(subprocess.run(
                    [FFPROBE, "-v", "error", "-show_entries",
                     "format=duration:stream=codec_type", "-of", "json", str(produced)],
                    capture_output=True, text=True, check=True, timeout=30).stdout)
                kinds = {s["codec_type"] for s in media["streams"]}
                assert {"video", "audio"} <= kinds, media
                assert 23 < float(media["format"]["duration"]) < 25, media
                print(f"[6] OUTPUT VERIFIED playable MP4 video+audio "
                      f"duration={media['format']['duration']}s")

                # Real cancellation of a live job.
                send(host, {"action": "assemble", "url": url, "output": "cancelled.mp4",
                            "jobId": "j2", "async": True})
                reader.wait_for(lambda m: m.get("action") == "assemble_started", 20, "start j2")
                time.sleep(2.0)
                send(host, {"action": "cancel", "jobId": "j2", "requestId": "c1"})
                ack, _ = reader.wait_for(
                    lambda m: m.get("action") == "cancel_result" and m.get("jobId") == "j2",
                    30, "cancel ack")
                assert ack["status"] == "cancelled", ack
                outcome, _ = reader.wait_for(
                    lambda m: m.get("action") == "assemble_result" and m.get("jobId") == "j2",
                    40, "cancelled result")
                assert outcome["status"] == "cancelled", outcome
                print(f"[7] CANCEL VERIFIED job={outcome['jobId']} status={outcome['status']}")
            finally:
                print("   host stderr:", " | ".join(err[-4:]) or "(empty)")
                host.terminate()
                host.wait(timeout=10)

            # ---------- Shipped default policy: private addresses refused -------
            host2, reader2, err2 = spawn_host(base_env, "strict")
            try:
                cases = [
                    ("loopback manifest", f"http://127.0.0.1:{port}/master.m3u8"),
                    ("non-http scheme", "file:///etc/passwd"),
                    ("credentials in url", "https://u:p@media.example.invalid/x.m3u8"),
                    ("not a playlist", f"http://127.0.0.1:{port}/segment-0.ts"),
                ]
                for label, bad in cases:
                    send(host2, {"action": "assemble", "url": bad,
                                 "output": "blocked.mp4", "jobId": f"b-{label}"})
                    refused, _ = reader2.wait_for(lambda m: m.get("action") == "error",
                                                  20, f"block {label}")
                    assert not (out_dir / "blocked.mp4").exists(), label
                    print(f"[8] STRICT BLOCKED [{label}]: {refused['error'][:110]}")

                # Browser must never relax the policy.
                send(host2, {"action": "assemble", "url": f"http://127.0.0.1:{port}/m.m3u8",
                             "output": "ovr.mp4", "jobId": "ovr", "allowLocal": True})
                refused, _ = reader2.wait_for(lambda m: m.get("action") == "error", 20, "override")
                assert "cannot be overridden" in refused["error"], refused
                print(f"[9] POLICY OVERRIDE REJECTED: {refused['error'][:90]}")
            finally:
                host2.terminate()
                host2.wait(timeout=10)

            # ---------- Nested SSRF, deterministic (mocked DNS) ----------------
            sys.path.insert(0, str(ROOT / "scripts"))
            from unittest.mock import patch
            import companion_host as ch

            def fake_getaddrinfo(host, port, **kwargs):
                # *.example.test is public; internal.corp rebinds to loopback.
                ip = "127.0.0.1" if host.endswith(".corp") else "93.184.216.34"
                return [(2, 1, 6, "", (ip, port or 443))]

            with patch("companion_host.socket.getaddrinfo", side_effect=fake_getaddrinfo):
                playlist = ("#EXTM3U\n#EXT-X-VERSION:3\n"
                            '#EXT-X-KEY:METHOD=AES-128,URI="http://internal.corp/key"\n'
                            "#EXTINF:2.0,\nhttp://internal.corp/seg.ts\n#EXT-X-ENDLIST\n")
                try:
                    ch.audit_nested_urls(playlist, "https://media.example.test/master.m3u8")
                    raise AssertionError("nested private reference was not blocked")
                except ch.MediaPolicyError as exc:
                    print(f"[10] NESTED SSRF BLOCKED: {str(exc)[:140]}")

                ok_playlist = ("#EXTM3U\n#EXT-X-VERSION:3\n#EXTINF:2.0,\n"
                               "https://cdn.example.test/seg1.ts\n#EXT-X-ENDLIST\n")
                findings = ch.audit_nested_urls(ok_playlist, "https://media.example.test/master.m3u8")
                assert findings["checked"] == 1 and findings["hosts"] == ["cdn.example.test"], findings
                print(f"[11] NESTED PUBLIC ALLOWED: {findings}")

            print("\nCOMPANION_PROTOCOL_TEST: ALL CHECKS PASSED")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
