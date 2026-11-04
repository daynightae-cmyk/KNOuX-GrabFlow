#!/usr/bin/env python3
"""Comprehensive security and contract tests for Native Companion Host."""

import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from companion_host import (
    CompanionHost, HOST_NAME, VERSION,
    read_message, write_message,
    validate_media_url, is_safe_destination,
    resolve_safe_output
)


class CompanionHostTests(unittest.TestCase):
    def setUp(self):
        self.host = CompanionHost(allow_local=True)

    def test_protocol_read_write(self):
        msg = {'action': 'ping', 'test': True}
        buf = io.BytesIO()
        write_message(msg, buf)
        buf.seek(0)
        read_back = read_message(buf)
        self.assertEqual(read_back, msg)

    def test_protocol_oversized_message_protection(self):
        # 20 MB message length header
        bad_header = struct.pack('<I', 20 * 1024 * 1024)
        buf = io.BytesIO(bad_header)
        with self.assertRaises(ValueError):
            read_message(buf)

    def test_ping_response_contract(self):
        resp = self.host.dispatch({'action': 'ping'})
        self.assertEqual(resp['action'], 'pong')
        self.assertEqual(resp['version'], VERSION)
        self.assertEqual(resp['host'], HOST_NAME)
        self.assertIn('ffmpegAvailable', resp)
        self.assertIn('ffprobeAvailable', resp)

    def test_ssrf_and_credential_rejections(self):
        strict_host = CompanionHost(allow_local=False)
        for url in (
            'https://user:pass@example.com/stream.m3u8',
            'file:///etc/passwd',
            'javascript:alert(1)',
            'https://127.0.0.1/stream.m3u8',
        ):
            # Direct helper, strict by default.
            with self.subTest(direct=url), self.assertRaises(ValueError):
                validate_media_url(url, allow_local=False)
            # And through the shipped dispatch path, so the policy cannot be
            # bypassed by choosing a different entry point.
            with self.subTest(dispatch=url), self.assertRaises(ValueError):
                strict_host.handle_probe({'url': url})

    def test_destination_safety_and_no_clobber(self):
        with tempfile.TemporaryDirectory() as td:
            temp_dir = Path(td)
            safe_file = temp_dir / 'output.mp4'
            self.assertTrue(is_safe_destination(safe_file))

            # Disallowed extension
            bad_ext = temp_dir / 'output.exe'
            self.assertFalse(is_safe_destination(bad_ext))

            # Existing file (no-clobber)
            safe_file.write_bytes(b'existing content')
            self.assertFalse(is_safe_destination(safe_file))

    def test_resolve_safe_output(self):
        p = resolve_safe_output('my_stream.mp4')
        self.assertTrue(p.is_absolute())
        self.assertEqual(p.suffix, '.mp4')
        self.assertTrue(str(p).endswith('my_stream.mp4'))

    def test_cancel_nonexistent_job(self):
        resp = self.host.dispatch({'action': 'cancel', 'jobId': 'job-999'})
        self.assertEqual(resp['action'], 'cancel_result')
        self.assertEqual(resp['status'], 'not_found')

    def test_unknown_action(self):
        resp = self.host.dispatch({'action': 'unsupported_command'})
        self.assertEqual(resp['action'], 'error')


if __name__ == '__main__':
    unittest.main()
