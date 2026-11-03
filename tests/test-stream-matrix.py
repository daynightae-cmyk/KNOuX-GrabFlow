#!/usr/bin/env python3
"""Real, offline-constructible HTTP HLS-master and DASH -> MP4 integration.

Requires FFmpeg and FFprobe. Missing tools are BLOCKED (nonzero), never PASS.
No real websites, credentials, DRM, or Chrome toolbar permissions are involved.
"""
from __future__ import annotations

import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSEMBLER = ROOT / "scripts" / "assemble_stream.py"


class SilentHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def run_checked(args: list[str], timeout: int = 60, cwd: Path | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=cwd)
    if result.returncode:
        raise AssertionError(
            f"Command failed with {result.returncode}: {args[0]}\n"
            f"{result.stderr[-2000:]}\n{result.stdout[-300:]}"
        )
    return result


def make_hls_variant(folder: Path, name: str, dimensions: str) -> None:
    run_checked([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-f", "lavfi", "-i", f"testsrc2=size={dimensions}:rate=12",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
        "-t", "3", "-c:v", "libx264", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-f", "hls", "-hls_time", "1", "-hls_playlist_type", "vod",
        "-hls_segment_filename", str(folder / f"{name}%d.ts"),
        str(folder / f"{name}.m3u8")
    ])


def make_dash(folder: Path) -> None:
    run_checked([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=12",
        "-f", "lavfi", "-i", "sine=frequency=660:sample_rate=44100",
        "-t", "3", "-c:v", "libx264", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-f", "dash", "-seg_duration", "1",
        "-use_template", "1", "-use_timeline", "1",
        "-adaptation_sets", "id=0,streams=v id=1,streams=a",
        str(folder / "manifest.mpd")
    ], cwd=folder)


def inspect_media(file: Path, expected_width: int) -> tuple[float, str]:
    assert file.is_file() and file.stat().st_size > 5000, "Missing or trivial output"
    result = run_checked([
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_type,width,height:format=duration,format_name",
        "-of", "json", str(file)
    ])
    info = json.loads(result.stdout)
    kinds = {item["codec_type"] for item in info["streams"]}
    assert {"video", "audio"}.issubset(kinds), kinds
    video = next(x for x in info["streams"] if x["codec_type"] == "video")
    assert video["width"] == expected_width, video
    duration = float(info["format"]["duration"])
    assert 2.5 < duration < 4.5, duration
    assert "mp4" in info["format"]["format_name"], info["format"]
    return duration, hashlib.sha256(file.read_bytes()).hexdigest()


class RealStreamMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            raise RuntimeError("BLOCKED: FFmpeg and FFprobe are mandatory for real stream matrix")
        cls.temp = tempfile.TemporaryDirectory(prefix="grabflow-stream-matrix-")
        cls.path = Path(cls.temp.name)
        try:
            make_hls_variant(cls.path, "high", "160x90")
            make_hls_variant(cls.path, "low", "96x54")
            (cls.path / "master.m3u8").write_text(
                "#EXTM3U\n#EXT-X-VERSION:3\n"
                "#EXT-X-STREAM-INF:BANDWIDTH=350000,RESOLUTION=160x90\nhigh.m3u8\n"
                "#EXT-X-STREAM-INF:BANDWIDTH=150000,RESOLUTION=96x54\nlow.m3u8\n",
                encoding="utf-8"
            )
            make_dash(cls.path)
            cls.server = ThreadingHTTPServer(
                ("127.0.0.1", 0),
                functools.partial(SilentHandler, directory=str(cls.path))
            )
            cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
            cls.worker.start()
            cls.origin = f"http://127.0.0.1:{cls.server.server_port}"
        except BaseException:
            cls.temp.cleanup()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join(timeout=5)
        cls.temp.cleanup()

    def assemble(self, playlist: str, dest: str, *, extension=".mp4"):
        out = self.path / (dest + extension)
        args = [
            sys.executable, str(ASSEMBLER),
            "--url", f"{self.origin}/{playlist}", "--output", str(out),
            "--allow-local"
        ]
        run_checked(args)
        duration, digest = inspect_media(out, expected_width=160)
        print(f"MEDIA_OK {playlist}: bytes={out.stat().st_size} duration={duration:.2f}s sha256={digest}")
        return out, args, digest

    def test_hls_master_variant_selection_and_no_overwrite(self):
        master = (self.path / "master.m3u8").read_text(encoding="utf-8")
        self.assertEqual(master.count("#EXT-X-STREAM-INF:"), 2)
        out, command, digest = self.assemble("master.m3u8", "hls-master")
        retry = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(retry.returncode, 0, "Existing file must not be overwritten")
        self.assertEqual(hashlib.sha256(out.read_bytes()).hexdigest(), digest)

    def test_dash_separate_audio_video_to_mp4(self):
        manifest = (self.path / "manifest.mpd").read_text(encoding="utf-8")
        self.assertIn("AdaptationSet", manifest)
        self.assemble("manifest.mpd", "dash-assembled")


if __name__ == "__main__":
    unittest.main(verbosity=2)
