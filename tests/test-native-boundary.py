#!/usr/bin/env python3
"""Native Messaging trust boundary: deterministic, offline regression coverage."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from companion_host import CompanionHost, resolve_safe_output, validate_media_url
from register_companion import build_manifest, register, validate_extension_id

GOOD_ID = "a" * 32


class TrustBoundaryTests(unittest.TestCase):
    def test_browser_cannot_override_loopback_block_on_probe(self):
        host = CompanionHost()
        for value in (True, False, "true"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "cannot be overridden"):
                host.handle_probe({"url": "http://127.0.0.1/stream.m3u8", "allowLocal": value})

    def test_browser_cannot_override_loopback_block_on_assemble(self):
        host = CompanionHost()
        with self.assertRaisesRegex(ValueError, "cannot be overridden"):
            host.handle_assemble({
                "url": "http://127.0.0.1/private.m3u8",
                "output": "video.mp4", "allowLocal": True,
            })

    def test_loopback_rejected_without_override_and_credentials_rejected(self):
        for url in (
            "http://127.0.0.1/private.m3u8",
            "http://[::1]/private.m3u8",
            "https://user:secret@example.org/video.mpd",
            "file:///etc/passwd",
            "https://example.org/watch",
            "https://example.org/" + "a" * 4100 + ".m3u8",
        ):
            with self.subTest(url=url[:60]), self.assertRaises(ValueError):
                validate_media_url(url)

    def test_dns_local_answer_denied_and_public_answer_allowed(self):
        with patch("companion_host.socket.getaddrinfo",
                   return_value=[(None, None, None, None, ("10.1.2.3", 443))]):
            with self.assertRaisesRegex(ValueError, "SSRF protection"):
                validate_media_url("https://media.example.test/master.m3u8")
        with patch("companion_host.socket.getaddrinfo",
                   return_value=[(None, None, None, None, ("1.1.1.1", 443))]):
            self.assertEqual(
                validate_media_url("https://media.example.test/master.m3u8").scheme,
                "https",
            )

    def test_output_paths_stay_within_downloads(self):
        for name in ("video.mp4", "KNOuX-GrabFlow/example.test/video.mp4", "movie.mkv"):
            with self.subTest(name=name):
                path = resolve_safe_output(name)
                self.assertEqual(path.name, Path(name).name)
                self.assertEqual(path.parent, (Path.home() / "Downloads"
                                 if (Path.home() / "Downloads").exists() else Path.home()).resolve())

    def test_output_rejects_traversal_and_absolute_destinations(self):
        for name in ("../escape.mp4", r"..\escape.mp4", r"C:\Windows\system32\escaped.mp4",
                     r"\\host\share\file.mp4", "/tmp/escaped.mp4", "CON.mp4", ""):
            with self.subTest(name=name), self.assertRaises(ValueError):
                resolve_safe_output(name)

    def test_extension_id_is_exact_not_wildcard(self):
        self.assertEqual(validate_extension_id(GOOD_ID), GOOD_ID)
        for value in (None, "*", "chrome-extension://*/", "A" * 32,
                      "z" * 32, "a" * 31, "a" * 33, "abc/../../", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_extension_id(value)

    def test_manifest_contains_exact_one_origin(self):
        manifest = build_manifest(GOOD_ID, r"C:\KNOuX\companion_host.bat")
        self.assertEqual(manifest["allowed_origins"], [f"chrome-extension://{GOOD_ID}/"])
        self.assertEqual(manifest["type"], "stdio")
        self.assertNotIn("*", json.dumps(manifest))

    def test_install_fails_before_any_file_or_registry_write_without_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"LOCALAPPDATA": tmp}):
                for value in (None, "*", "invalid"):
                    with self.subTest(value=value), self.assertRaises(ValueError):
                        register(value)
                self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_source_manifest_has_no_wildcard_or_implicit_origins(self):
        template = json.loads((ROOT / "scripts" / "com.knoux.grabflow.companion.json").read_text(encoding="utf-8"))
        self.assertEqual(template["allowed_origins"], [])


if __name__ == "__main__":
    unittest.main()
