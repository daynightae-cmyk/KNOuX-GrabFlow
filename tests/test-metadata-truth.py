#!/usr/bin/env python3
"""Regression tests for the v0.6.7 metadata-truth and audit-wording fixes.

Defect A: ffprobe reports the byte size of an HLS/DASH playlist in
``format.size``. That number must never be presented as the size of the media
the playlist describes, and a missing/zero bitrate must not become ``0 kbps``.

Defect B: a relaxed-policy audit was described as "verified public". The audit
only proves that references were checked against the active policy; it cannot
claim they are public when loopback is deliberately allowed for a fixture.
The wording must say that, while the actual network policy stays enforced.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "scripts"))

import media_tools  # noqa: E402
from companion_host import (  # noqa: E402
    CompanionHost,
    MediaPolicyError,
    _is_stream_manifest,
    _normalize_probe_metadata,
    audit_nested_urls,
)


class MetadataNormalizationTests(unittest.TestCase):
    def test_hls_manifest_size_is_labelled_not_reported_as_media(self):
        metadata = _normalize_probe_metadata(
            {"format_name": "hls", "duration": "16.0", "size": "345", "bit_rate": "0"},
            "https://cdn.example.test/master.m3u8",
        )
        self.assertEqual(metadata["sizeSource"], "manifest")
        self.assertIsNone(metadata["sizeBytes"])
        self.assertEqual(metadata["manifestBytes"], 345)
        self.assertIsNone(metadata["bitRate"])
        self.assertEqual(metadata["bitRateSource"], "unavailable")
        self.assertEqual(metadata["durationSeconds"], 16.0)

    def test_dash_manifest_is_detected_even_without_an_extension(self):
        metadata = _normalize_probe_metadata(
            {"format_name": "dash", "duration": "4.0", "size": "900"},
            "https://cdn.example.test/manifest?token=abc",
        )
        self.assertEqual(metadata["sizeSource"], "manifest")
        self.assertIsNone(metadata["sizeBytes"])
        self.assertEqual(metadata["manifestBytes"], 900)
        self.assertIsNone(metadata["bitRate"])

    def test_manifest_detection_falls_back_to_the_url_path(self):
        self.assertTrue(_is_stream_manifest("", "https://cdn.example.test/a.m3u8"))
        self.assertTrue(_is_stream_manifest("", "https://cdn.example.test/a.MPD"))
        self.assertFalse(_is_stream_manifest("", "https://cdn.example.test/a.mp4"))

    def test_direct_media_size_and_positive_bitrate_are_preserved(self):
        metadata = _normalize_probe_metadata(
            {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "16.0",
             "size": "1042878", "bit_rate": "521439"},
            "https://cdn.example.test/clip.mp4",
        )
        self.assertEqual(metadata["sizeSource"], "media")
        self.assertEqual(metadata["sizeBytes"], 1042878)
        self.assertIsNone(metadata["manifestBytes"])
        self.assertEqual(metadata["bitRate"], 521439)
        self.assertEqual(metadata["bitRateSource"], "media")

    def test_zero_or_missing_measurements_become_unknown_not_zero(self):
        for fmt in (
            {"format_name": "mov,mp4", "size": "1234", "bit_rate": "0"},
            {"format_name": "mov,mp4", "size": "1234"},
            {"format_name": "mov,mp4", "size": "0", "bit_rate": "N/A"},
            {},
        ):
            with self.subTest(fmt=fmt):
                metadata = _normalize_probe_metadata(fmt, "https://cdn.example.test/clip.mp4")
                self.assertIsNone(metadata["bitRate"])
                self.assertEqual(metadata["bitRateSource"], "unavailable")
                self.assertNotEqual(metadata["bitRate"], 0)

    def test_missing_manifest_size_is_unknown(self):
        metadata = _normalize_probe_metadata(
            {"format_name": "hls", "duration": "16.0", "bit_rate": "0"},
            "https://cdn.example.test/master.m3u8",
        )
        self.assertEqual(metadata["sizeSource"], "manifest")
        self.assertIsNone(metadata["manifestBytes"])
        self.assertIsNone(metadata["sizeBytes"])


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class RealPlaylistProbeTests(unittest.TestCase):
    """The actual ffprobe/HLS path that produced the misleading 345 B result."""

    @classmethod
    def setUpClass(cls):
        cls.ffmpeg, cls.ffprobe = media_tools.pair()
        if not (cls.ffmpeg and cls.ffprobe and Path(cls.ffmpeg).is_file()):
            raise unittest.SkipTest("FFmpeg/FFprobe unavailable")
        cls.tmp = tempfile.TemporaryDirectory(prefix="grabflow-metadata-")
        cls.fixtures = Path(cls.tmp.name)
        subprocess.run([
            cls.ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
            "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=10",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
            "-t", "3", "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-f", "hls", "-hls_time", "1", "-hls_list_size", "0",
            "-hls_playlist_type", "vod", str(cls.fixtures / "master.m3u8"),
        ], check=True, capture_output=True, timeout=180)
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(QuietHandler, directory=str(cls.fixtures)))
        Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/master.m3u8"

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "server", None):
            cls.server.shutdown()
            cls.server.server_close()
        if getattr(cls, "tmp", None):
            cls.tmp.cleanup()

    def test_real_hls_probe_distinguishes_manifest_from_media(self):
        host = CompanionHost(allow_local=True)
        response = host.handle_probe({"url": self.url})
        self.assertEqual(response["status"], "ok", response)
        self.assertEqual(response["sizeSource"], "manifest")
        self.assertIsNone(response["sizeBytes"])
        self.assertIsNone(response["bitRate"])
        self.assertEqual(response["bitRateSource"], "unavailable")
        self.assertGreater(response["durationSeconds"], 2.0)
        self.assertLess(response["durationSeconds"], 4.5)
        self.assertTrue(response["videoTracks"], response)
        self.assertTrue(response["audioTracks"], response)
        # The raw manifest is small; the produced programme is much larger.
        manifest_size = (self.fixtures / "master.m3u8").stat().st_size
        if response["manifestBytes"] is not None:
            self.assertEqual(response["manifestBytes"], manifest_size)
        segment_size = (self.fixtures / "master0.ts").stat().st_size
        self.assertGreater(segment_size, manifest_size * 10)


class AuditTruthAndPolicyTests(unittest.TestCase):
    def test_audit_wording_no_longer_claims_references_are_public(self):
        source = (ROOT / "popup.js").read_text(encoding="utf-8")
        self.assertNotIn("verified public", source)
        self.assertNotIn("تحققت أنها عامة", source)
        self.assertIn("references checked", source)
        self.assertIn("تم فحص", source)
        self.assertIn("auditPassed", source)

    def test_nested_loopback_reference_is_still_rejected(self):
        playlist = ("#EXTM3U\n#EXTINF:2.0,\n"
                    "http://127.0.0.1/private.ts\n#EXT-X-ENDLIST\n")
        with self.assertRaisesRegex(MediaPolicyError, "SSRF protection"):
            audit_nested_urls(playlist, "https://cdn.example.test/master.m3u8",
                              allow_local=False)

    def test_nested_file_and_script_references_are_still_rejected(self):
        for reference in ("file:///etc/passwd", "javascript:alert(1)"):
            with self.subTest(reference=reference):
                playlist = f"#EXTM3U\n#EXTINF:2.0,\n{reference}\n#EXT-X-ENDLIST\n"
                with self.assertRaises(MediaPolicyError):
                    audit_nested_urls(playlist, "https://cdn.example.test/master.m3u8",
                                      allow_local=False)

    def test_public_nested_reference_passes_without_a_public_claim(self):
        with patch(
                "companion_host.socket.getaddrinfo",
                return_value=[(None, None, None, None, ("1.1.1.1", 443))]):
            findings = audit_nested_urls(
                "#EXTM3U\n#EXTINF:2.0,\nhttps://cdn.example.test/seg.ts\n",
                "https://cdn.example.test/master.m3u8")
        self.assertEqual(findings["checked"], 1)
        self.assertEqual(findings["hosts"], ["cdn.example.test"])
        # The result is an audit count, not a claim that the host is public.
        self.assertNotIn("public", json.dumps(findings).lower())


if __name__ == "__main__":
    unittest.main()
