#!/usr/bin/env python3
"""Optional desktop companion for user-owned, unprotected HLS/DASH media.

Runs a locally installed FFmpeg executable; it is NOT part of the Chrome extension.
No secrets, cookies, authentication, decryption, bypass or browser interception.
"""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from urllib.parse import urlsplit


def validate(url: str, output: Path, *, allow_local=False):
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Only HTTP(S) media URLs without embedded credentials are supported')
    path = parsed.path.lower()
    if not path.endswith(('.m3u8', '.mpd')) and 'm3u8' not in parsed.query.lower() and 'mpd' not in parsed.query.lower():
        raise ValueError('URL path must be an HLS .m3u8 or DASH .mpd playlist')
    if output.suffix.lower() not in ('.mp4', '.mkv'):
        raise ValueError('Output filename must end in .mp4 or .mkv')
    if output.exists():
        raise ValueError('Refusing to overwrite an existing output file')
    if not allow_local:
        for addr in socket.getaddrinfo(parsed.hostname, None, type=socket.SOCK_STREAM):
            ip = ipaddress.ip_address(addr[4][0])
            if not ip.is_global:
                raise ValueError('Local/private-network URL blocked by default; use --allow-local for a controlled fixture')
    return parsed


def find_ffmpeg(custom: str = 'ffmpeg'):
    binary = shutil.which(custom)
    if not binary and sys.platform == 'win32':
        candidates = [
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'ffmpeg' / 'bin' / 'ffmpeg.exe',
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'WinGet' / 'Links' / 'ffmpeg.exe',
            Path(r'C:\ffmpeg\bin\ffmpeg.exe'),
            Path(r'C:\ProgramData\chocolatey\bin\ffmpeg.exe'),
            Path(os.environ.get('USERPROFILE', '')) / 'scoop' / 'apps' / 'ffmpeg' / 'current' / 'bin' / 'ffmpeg.exe',
        ]
        for c in candidates:
            if c.is_file():
                return str(c)
    return binary


def make_command(ffmpeg: str, url: str, output: Path):
    return [ffmpeg, '-hide_banner', '-nostdin', '-loglevel', 'warning',
            '-i', url, '-c', 'copy',
            '-movflags', '+faststart', '-n', str(output)]


def main():
    ap = argparse.ArgumentParser(description='Assemble authorized unprotected HLS/DASH stream into MP4/MKV.')
    ap.add_argument('--url', required=True, help='Direct playlist URL (.m3u8 or .mpd)')
    ap.add_argument('--output', required=True, type=Path, help='New .mp4 or .mkv file (never overwritten)')
    ap.add_argument('--ffmpeg', default='ffmpeg', help='Path to local FFmpeg executable')
    ap.add_argument('--allow-local', action='store_true', help='For controlled local test fixtures only')
    ap.add_argument('--dry-run', action='store_true', help='Print command without downloading')
    a = ap.parse_args()
    try:
        validate(a.url, a.output, allow_local=a.allow_local)
        ffmpeg = find_ffmpeg(a.ffmpeg)
        if not ffmpeg:
            raise RuntimeError('FFmpeg is not installed or not on PATH')
        if not a.output.parent.exists():
            raise ValueError('Output directory does not exist')
        command = make_command(ffmpeg, a.url, a.output)
        if a.dry_run:
            print(json.dumps({'command': command, 'note': 'This URL is a playlist, not an MP4 file.'}, ensure_ascii=False))
            return 0
        print('Assembling stream into a single playable media file; no overwrite enabled.', flush=True)
        result = subprocess.run(command, check=False, timeout=3600)
        if result.returncode:
            print('FFmpeg failed (possibly unavailable segments, codec mismatch, DRM or network error).', flush=True)
            return result.returncode
        if not a.output.is_file() or a.output.stat().st_size == 0:
            print('FFmpeg reported success but the output is missing or empty.', flush=True)
            return 8
        print(json.dumps({'state': 'complete', 'output': str(a.output), 'bytes': a.output.stat().st_size}))
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        ap.exit(2, f'ERROR: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
