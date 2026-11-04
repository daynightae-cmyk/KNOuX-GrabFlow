"""Safety and no-clobber tests for optional FFmpeg companion."""
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from assemble_stream import (validate, make_command, canonical_playlist_url,
                             assert_argv_safe, run_assembly)

class CompanionTests(unittest.TestCase):
    def test_accepts_hls_dash_and_querystrings(self):
        with TemporaryDirectory() as d:
            for url in ('https://media.example.com/movie.m3u8?token=redacted', 'https://media.example.com/master.mpd'):
                self.assertEqual(validate(url, Path(d)/'movie.mp4', allow_local=True).scheme, 'https')
    def test_rejects_non_playlist_and_credentials(self):
        with TemporaryDirectory() as d:
            for url in ('file:///etc/passwd', 'javascript:alert(1)', 'https://u:p@example.com/movie.m3u8', 'https://example.com/watch'):
                with self.assertRaises(ValueError): validate(url, Path(d)/'test.mp4')
    def test_no_overwrite(self):
        with TemporaryDirectory() as d:
            path=Path(d)/'movie.mp4'
            path.write_bytes(b'keep')
            with self.assertRaises(ValueError): validate('https://example.com/movie.m3u8', path)
            self.assertEqual(path.read_bytes(), b'keep')
    def test_avoids_shell_and_overwrite(self):
        cmd=make_command('/usr/bin/ffmpeg', 'https://example.com/test.m3u8', Path('out.mp4'))
        self.assertEqual(cmd[0], '/usr/bin/ffmpeg')
        self.assertIn('-n', cmd)
        self.assertNotIn('-y', cmd)
        self.assertNotIn('-map', cmd) # FFmpeg auto-selects a video/audio stream

    def test_playlist_url_allowlist_rejects_argument_shaped_input(self):
        """The URL reaching FFmpeg is rebuilt from an allowlisted form."""
        for good in ('https://cdn.example.com/master.m3u8',
                     'http://127.0.0.1:8080/a.m3u8?t=1&x=2',
                     'https://example.com/a.mpd'):
            self.assertEqual(canonical_playlist_url(good), good)
        for bad in ('-i', 'file:///etc/passwd', 'https://e.com/a b.m3u8',
                    'https://e.com/"x.m3u8', 'https://u:p@e.com/a.m3u8',
                    'https://e.com/a.m3u8; rm -rf /'):
            with self.subTest(url=bad[:40]), self.assertRaises(ValueError):
                canonical_playlist_url(bad)

    def test_argv_guard_rejects_empty_and_control_characters(self):
        checked = assert_argv_safe(['/x/ffmpeg', '-i', 'https://e.com/a.m3u8'])
        self.assertEqual(checked[1], '-i')
        nul = 'a' + chr(0) + 'b'
        newline = 'a' + chr(10) + 'b'
        for bad in ([], ['ok', ''], ['ok', None], ['ok', nul], ['ok', newline]):
            with self.subTest(argv=bad), self.assertRaises(ValueError):
                assert_argv_safe(bad)

    def test_run_assembly_refuses_a_relative_executable(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                run_assembly('ffmpeg', 'https://e.com/a.m3u8', Path(d) / 'out.mp4')

if __name__ == '__main__': unittest.main()
