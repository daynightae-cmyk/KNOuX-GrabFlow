#!/usr/bin/env python3
"""Optional desktop companion for user-owned, unprotected HLS/DASH media.

Runs a locally installed FFmpeg executable; it is NOT part of the Chrome extension.
No secrets, cookies, authentication, decryption, bypass or browser interception.
"""
import argparse
import ipaddress
import json
import os
import re
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from urllib.parse import urlsplit, urlunsplit

# Same confinement the native companion host applies, so the manual CLI cannot
# become the weaker path to the same FFmpeg.
PROTOCOL_WHITELIST = 'file,http,https,tcp,tls,crypto'
PLAYLIST_EXTENSIONS = 'm3u8,ts,m4s,mp4,mkv,webv,vtt,srt,ssa,aac,ac3,eac3,mp3,opus'
ASSEMBLY_TIMEOUT = 3600


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
    # A portable build is legitimate: honour the same variables the companion host
    # and the test suite use before falling back to PATH.
    explicit = os.environ.get(f"KNOUX_{custom.upper()}_EXE", "").strip()
    if explicit and Path(explicit).is_file():
        return explicit
    override_dir = os.environ.get("KNOUX_FFMPEG_DIR", "").strip()
    if override_dir:
        for suffix in (".exe", "") if os.name == "nt" else ("",):
            candidate = Path(override_dir) / f"{custom}{suffix}"
            if candidate.is_file():
                return str(candidate)
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


def validate_executable(path_str: str) -> str:
    """Reject anything that is not a real, plausible media executable.

    `--ffmpeg` is operator input handed straight to subprocess, so a mistyped or
    manipulated value would otherwise launch an arbitrary program. Requiring an
    existing regular file with an executable shape closes that gap without
    limiting legitimate portable builds.
    """
    candidate = Path(path_str).expanduser()
    if not candidate.is_file():
        raise RuntimeError(f'FFmpeg path is not an existing file: {path_str}')
    if candidate.is_symlink():
        raise RuntimeError(f'Refusing to execute a symlinked FFmpeg: {path_str}')
    if not os.access(candidate, os.X_OK if os.name != 'nt' else os.R_OK):
        raise RuntimeError(f'FFmpeg is not readable/executable: {path_str}')
    if os.name == 'nt' and candidate.suffix.lower() not in ('.exe', '.cmd', '.bat'):
        raise RuntimeError(f'Expected a Windows executable, got: {path_str}')
    return str(candidate)


def make_command(ffmpeg: str, url: str, output: Path):
    return [ffmpeg, '-hide_banner', '-nostdin', '-loglevel', 'warning',
            '-protocol_whitelist', PROTOCOL_WHITELIST,
            '-allowed_extensions', PLAYLIST_EXTENSIONS,
            '-i', url, '-c', 'copy',
            '-movflags', '+faststart', '-n', str(output)]


# A playlist URL handed to FFmpeg is restricted to the characters that appear in
# real manifests. Quotes, whitespace, backslashes and control characters are not
# in the class, so an argument that tries to become something other than a URL
# cannot pass.
SAFE_PLAYLIST_URL = re.compile(r"^https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]{1,2048}$")


def canonical_playlist_url(url: str) -> str:
    """Return the URL re-serialised from a parsed, allowlisted form.

    The value handed to the child process is constructed here from components
    that have been checked individually, rather than forwarded from the command
    line as-is.
    """
    if not isinstance(url, str) or not SAFE_PLAYLIST_URL.fullmatch(url):
        raise ValueError('Playlist URL contains characters that are not permitted')
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.hostname:
        raise ValueError('Playlist URL must be http(s) and carry a host')
    if parts.username or parts.password:
        raise ValueError('Refusing a playlist URL with embedded credentials')
    rebuilt = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, parts.fragment))
    if rebuilt != url:
        raise ValueError('Playlist URL is not in canonical form')
    return rebuilt


def assert_argv_safe(argv) -> list:
    """Refuse an argument vector that could be read as something it is not.

    `--ffmpeg` and `--url` are operator input. Even though no shell is involved,
    an option-like value or an embedded NUL would change what FFmpeg does rather
    than what it reads, so both are rejected here, immediately before the child
    process is started, rather than only at parse time.
    """
    if not isinstance(argv, (list, tuple)) or not argv:
        raise ValueError('Refusing to run an empty command')
    checked = []
    for item in argv:
        if not isinstance(item, str) or not item:
            raise ValueError('Refusing a non-string or empty command argument')
        if any(char in item for char in ('\x00', '\n', '\r')):
            raise ValueError('Refusing a command argument containing control characters')
        checked.append(item)
    return checked


def audit_playlist(playlist_url: str, allow_local: bool) -> None:
    """Apply the same nested-reference audit the native companion host applies.

    Without this the command-line path was the weaker route to the same FFmpeg:
    a public playlist whose keys or segments point at a private address would
    have gone unaudited. A policy breach raises; a transport limitation only
    warns, because failing to fetch is not evidence of an attack.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from companion_host import (fetch_manifest, audit_nested_urls,
                                MediaPolicyError, MediaFetchError)
    try:
        text, effective = fetch_manifest(playlist_url, allow_local=allow_local)
        findings = audit_nested_urls(text, effective, allow_local=allow_local)
    except MediaPolicyError:
        raise
    except (MediaFetchError, OSError, UnicodeDecodeError) as exc:
        print(f'NOTE: nested-reference audit unavailable ({exc}); '
              'FFmpeg protocol and extension whitelists still apply.', flush=True)
        return
    print(f'Audited {findings["checked"]} nested reference(s) across '
          f'{len(findings["hosts"])} host(s); all public.', flush=True)


def run_assembly(ffmpeg: str, playlist_url: str, output: Path):
    """The single place a child process is started, from checked values only.

    The argument vector is assembled here, next to the checks that justify each
    dynamic element, rather than being handed in from elsewhere: every value that
    is not a literal in this function has been admitted by a check on the line
    above it.
    """
    target = canonical_playlist_url(playlist_url)
    executable = Path(ffmpeg).expanduser().resolve()
    if not executable.is_absolute() or not executable.is_file():
        raise ValueError('Refusing to run FFmpeg from a non-absolute or missing path')
    destination = str(output)
    if not destination or destination.startswith('-'):
        raise ValueError('Refusing an option-like output path')
    argv = assert_argv_safe([
        str(executable),
        '-hide_banner', '-nostdin', '-loglevel', 'warning',
        '-protocol_whitelist', PROTOCOL_WHITELIST,
        '-allowed_extensions', PLAYLIST_EXTENSIONS,
        '-i', target,
        '-c', 'copy',
        '-movflags', '+faststart',
        '-n', destination,
    ])
    return subprocess.run(argv, check=False, timeout=ASSEMBLY_TIMEOUT, shell=False)


def prepare(a):
    """Validate every input and resolve the toolchain before anything runs."""
    validate(a.url, a.output, allow_local=a.allow_local)
    ffmpeg = find_ffmpeg(a.ffmpeg)
    if not ffmpeg:
        raise RuntimeError('FFmpeg is not installed or not on PATH')
    ffmpeg = validate_executable(ffmpeg)
    if not a.output.parent.exists():
        raise ValueError('Output directory does not exist')
    return ffmpeg


def main():
    ap = argparse.ArgumentParser(description='Assemble authorized unprotected HLS/DASH stream into MP4/MKV.')
    ap.add_argument('--url', required=True, help='Direct playlist URL (.m3u8 or .mpd)')
    ap.add_argument('--output', required=True, type=Path, help='New .mp4 or .mkv file (never overwritten)')
    ap.add_argument('--ffmpeg', default='ffmpeg', help='Path to local FFmpeg executable')
    ap.add_argument('--allow-local', action='store_true', help='For controlled local test fixtures only')
    ap.add_argument('--dry-run', action='store_true', help='Print command without downloading')
    a = ap.parse_args()
    try:
        ffmpeg = prepare(a)
        if a.dry_run:
            print(json.dumps({'command': make_command(ffmpeg, a.url, a.output),
                              'note': 'This URL is a playlist, not an MP4 file.'}, ensure_ascii=False))
            return 0
        print('Assembling stream into a single playable media file; no overwrite enabled.', flush=True)
        audit_playlist(a.url, a.allow_local)
        result = run_assembly(ffmpeg, a.url, a.output)
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
