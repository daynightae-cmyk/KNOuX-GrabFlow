"""Safety and no-clobber tests for optional FFmpeg companion."""
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from assemble_stream import validate, make_command

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

if __name__ == '__main__': unittest.main()
