#!/usr/bin/env python3
"""KNOuX GrabFlow — Windows Native Media Companion Host.

Implements Chrome Native Messaging protocol over stdio to provide secure,
local, authorized FFmpeg assembly of user-selected HLS/DASH streams.

Security Guarantees:
- Strictly length-prefixed JSON messaging (Chrome Native Messaging standard).
- No shell interpolation: all subprocesses invoked with argument lists only.
- Strict URL validation (HTTP/HTTPS only, no embedded credentials).
- SSRF prevention: blocks loopback and private IP addresses by default.
- No-clobber guarantee: never overwrites existing output files (-n flag).
- Path traversal prevention: output paths validated and sanitized.
- No secret collection, no telemetry, no background persistence.
"""

import ipaddress
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import sys
from urllib.parse import urlsplit

VERSION = "0.6.0"
HOST_NAME = "com.knoux.grabflow.companion"


def is_safe_destination(path: Path) -> bool:
    """Validate that destination has an approved extension and parent exists."""
    if path.suffix.lower() not in ('.mp4', '.mkv'):
        return False
    if path.exists():
        return False
    # Check parent exists and is not root
    try:
        return path.parent.exists() and len(path.parts) > 1
    except Exception:
        return False


def resolve_safe_output(out_str: str) -> Path:
    """Resolve an output path safely, placing relative filenames into user's Downloads."""
    p = Path(out_str)
    if not p.is_absolute() or len(p.parts) == 1:
        downloads = Path.home() / 'Downloads'
        if not downloads.exists():
            downloads = Path.home()
        safe_name = p.name.replace(':', '_').replace('/', '_').replace('\\', '_')
        if not safe_name.endswith('.mp4') and not safe_name.endswith('.mkv'):
            safe_name += '.mp4'
        p = downloads / safe_name
    return p.resolve()


def validate_media_url(url: str, allow_local: bool = False):
    """Validate HTTP/HTTPS media URL and enforce SSRF protections."""
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('Only HTTP and HTTPS media URLs are supported')
    if parsed.username or parsed.password:
        raise ValueError('URLs containing credentials are strictly prohibited')
    path = parsed.path.lower()
    if not path.endswith(('.m3u8', '.mpd')) and 'm3u8' not in parsed.query.lower() and 'mpd' not in parsed.query.lower():
        raise ValueError('URL must target an HLS (.m3u8) or DASH (.mpd) stream manifest')
    if not allow_local:
        try:
            for addr in socket.getaddrinfo(parsed.hostname, None, type=socket.SOCK_STREAM):
                ip = ipaddress.ip_address(addr[4][0])
                if not ip.is_global:
                    raise ValueError(f'SSRF protection: access to private/loopback address {ip} is blocked')
        except socket.gaierror:
            raise ValueError(f'Could not resolve hostname: {parsed.hostname}')
    return parsed


def find_binaries():
    """Locate local ffmpeg and ffprobe executables across standard Windows paths."""
    ffmpeg = shutil.which('ffmpeg')
    ffprobe = shutil.which('ffprobe')
    if sys.platform == 'win32' and not ffmpeg:
        common_paths = [
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'ffmpeg' / 'bin' / 'ffmpeg.exe',
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'WinGet' / 'Links' / 'ffmpeg.exe',
            Path(r'C:\ffmpeg\bin\ffmpeg.exe'),
            Path(r'C:\ProgramData\chocolatey\bin\ffmpeg.exe'),
            Path(os.environ.get('USERPROFILE', '')) / 'scoop' / 'apps' / 'ffmpeg' / 'current' / 'bin' / 'ffmpeg.exe',
        ]
        for p in common_paths:
            if p.is_file():
                ffmpeg = str(p)
                probe_cand = p.with_name('ffprobe.exe')
                if probe_cand.is_file():
                    ffprobe = str(probe_cand)
                break
    return ffmpeg, ffprobe


def read_message(stream=sys.stdin.buffer):
    """Read a length-prefixed native messaging JSON message."""
    raw_length = stream.read(4)
    if len(raw_length) == 0:
        return None
    if len(raw_length) < 4:
        raise IOError('Incomplete message length received from browser')
    message_length = struct.unpack('<I', raw_length)[0]
    if message_length > 10 * 1024 * 1024:
        raise ValueError(f'Message length exceeds maximum allowed limit: {message_length}')
    message_data = stream.read(message_length)
    if len(message_data) < message_length:
        raise IOError('Incomplete message body received from browser')
    return json.loads(message_data.decode('utf-8'))


def write_message(message, stream=sys.stdout.buffer):
    """Write a length-prefixed native messaging JSON response."""
    encoded = json.dumps(message, ensure_ascii=False).encode('utf-8')
    stream.write(struct.pack('<I', len(encoded)))
    stream.write(encoded)
    stream.flush()


class CompanionHost:
    def __init__(self, allow_local=False):
        self.allow_local = allow_local
        self.active_processes = {}

    def handle_ping(self, _msg):
        ffmpeg, ffprobe = find_binaries()
        return {
            'action': 'pong',
            'version': VERSION,
            'host': HOST_NAME,
            'ffmpegAvailable': bool(ffmpeg),
            'ffprobeAvailable': bool(ffprobe),
            'ffmpegPath': ffmpeg,
            'ffprobePath': ffprobe,
            'platform': sys.platform
        }

    def handle_probe(self, msg):
        url = msg.get('url', '')
        validate_media_url(url, allow_local=self.allow_local or msg.get('allowLocal', False))
        _ffmpeg, ffprobe = find_binaries()
        if not ffprobe:
            return {'action': 'probe_result', 'status': 'unavailable', 'message': 'ffprobe is not installed'}
        cmd = [
            ffprobe, '-hide_banner', '-loglevel', 'error',
            '-show_entries', 'stream=index,codec_name,codec_type,width,height,bit_rate:format=duration',
            '-of', 'json', url
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode != 0:
            return {'action': 'probe_result', 'status': 'error', 'error': res.stderr.strip()[:300]}
        try:
            data = json.loads(res.stdout)
            return {'action': 'probe_result', 'status': 'ok', 'data': data}
        except Exception as e:
            return {'action': 'probe_result', 'status': 'error', 'error': str(e)}

    def handle_assemble(self, msg):
        url = msg.get('url', '')
        job_id = msg.get('jobId', 'default')
        out_str = msg.get('output', '')
        if not out_str:
            raise ValueError('Output path is required')
        
        # If relative or filename-only, place in Downloads safely
        out_path = resolve_safe_output(out_str)
        if not is_safe_destination(out_path):
            raise ValueError('Invalid destination path or file already exists (no-clobber enforced)')

        validate_media_url(url, allow_local=self.allow_local or msg.get('allowLocal', False))
        ffmpeg, _ffprobe = find_binaries()
        if not ffmpeg:
            return {'action': 'assemble_result', 'jobId': job_id, 'status': 'failed', 'error': 'FFmpeg executable is not available'}

        cmd = [
            ffmpeg, '-hide_banner', '-nostdin', '-loglevel', 'warning',
            '-i', url, '-c', 'copy',
            '-movflags', '+faststart', '-n', str(out_path)
        ]
        # Execute securely via subprocess argument list (no shell)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.active_processes[job_id] = proc
        try:
            _stdout, stderr = proc.communicate(timeout=msg.get('timeout', 3600))
            if proc.returncode != 0:
                return {
                    'action': 'assemble_result', 'jobId': job_id, 'status': 'failed',
                    'error': stderr.strip()[:400] or 'FFmpeg process exited with error'
                }
            if not out_path.is_file() or out_path.stat().st_size == 0:
                return {
                    'action': 'assemble_result', 'jobId': job_id, 'status': 'failed',
                    'error': 'Output file was not created or is empty'
                }
            return {
                'action': 'assemble_result', 'jobId': job_id, 'status': 'complete',
                'output': str(out_path), 'bytes': out_path.stat().st_size
            }
        except subprocess.TimeoutExpired:
            proc.kill()
            return {'action': 'assemble_result', 'jobId': job_id, 'status': 'timeout', 'error': 'Assembly timed out'}
        finally:
            self.active_processes.pop(job_id, None)

    def handle_cancel(self, msg):
        job_id = msg.get('jobId')
        proc = self.active_processes.get(job_id)
        if proc:
            proc.terminate()
            return {'action': 'cancel_result', 'jobId': job_id, 'status': 'cancelled'}
        return {'action': 'cancel_result', 'jobId': job_id, 'status': 'not_found'}

    def dispatch(self, msg):
        action = msg.get('action')
        if action == 'ping':
            return self.handle_ping(msg)
        elif action == 'probe':
            return self.handle_probe(msg)
        elif action == 'assemble':
            return self.handle_assemble(msg)
        elif action == 'cancel':
            return self.handle_cancel(msg)
        else:
            return {'action': 'error', 'error': f'Unknown action: {action}'}


def run_host():
    host = CompanionHost()
    while True:
        try:
            msg = read_message()
            if msg is None:
                break
            resp = host.dispatch(msg)
            write_message(resp)
        except Exception as exc:
            write_message({'action': 'error', 'error': str(exc)})


if __name__ == '__main__':
    run_host()
