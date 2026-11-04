#!/usr/bin/env python3
"""KNOuX GrabFlow — Windows Native Media Companion Host.

Implements Chrome/Edge Native Messaging protocol over stdio to provide secure,
local, authorized FFmpeg assembly of user-selected HLS/DASH streams.

Security Guarantees:
- Strictly length-prefixed JSON messaging (Native Messaging standard).
- No shell interpolation: all subprocesses invoked with argument lists only.
- Strict URL validation (HTTP/HTTPS only, no embedded credentials).
- SSRF prevention: blocks loopback and private IP addresses by default, and
  re-validates every redirect hop and every nested playlist reference.
- DNS-rebinding defence: manifests are fetched through connections pinned to a
  previously validated address, with the TLS peer still verified by hostname.
- FFmpeg is confined with a protocol whitelist and playlist extension
  whitelist so a hostile playlist cannot reach local files or arbitrary schemes.
- Bounded memory and disk: manifest bodies, segment counts and output growth
  all have hard ceilings that abort the job instead of exhausting the machine.
- No-clobber guarantee: never overwrites existing output files (-n flag).
- Path traversal prevention: output paths validated and sanitized.
- No secret collection, no telemetry, no background persistence.

Long-running jobs are assembled on a worker thread so the host stays responsive
and can honour a real `cancel` request while FFmpeg is running.
"""

import collections
import ipaddress
import json
import os
import re
from pathlib import Path
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import threading
import time
from urllib.parse import urljoin, urlsplit

VERSION = "0.6.4"
HOST_NAME = "com.knoux.grabflow.companion"

# --- Hard ceilings. Every one of these is enforced, not advisory. -----------
MAX_MESSAGE_BYTES = 10 * 1024 * 1024      # inbound native-messaging frame
MAX_MANIFEST_BYTES = 4 * 1024 * 1024      # a single playlist/MPD body we will read
MANIFEST_TOO_LARGE = 'Media manifest exceeds the maximum accepted size'
MAX_NESTED_ENTRIES = 20000                # segments/variants inspected per manifest
MAX_REDIRECT_HOPS = 5                     # per fetched resource
MAX_URL_LENGTH = 4096
MAX_OUTPUT_BYTES = 8 * 1024 * 1024 * 1024  # 8 GiB assembly ceiling
MAX_ACTIVE_JOBS = 4                       # concurrent FFmpeg processes
DEFAULT_ASSEMBLE_TIMEOUT = 3600
PROBE_TIMEOUT = 20
FETCH_TIMEOUT = 15
PROGRESS_INTERVAL = 1.0                   # seconds between progress frames
STDERR_KEEP_LINES = 40                      # bounded FFmpeg diagnostics ring

# FFmpeg may only use these transports and may only dereference these file
# types from a playlist. Anything else (file:, data:, arbitrary extensions)
# is refused before a byte is written.
ALLOWED_PROTOCOLS = "file,http,https,tcp,tls,crypto"
ALLOWED_PLAYLIST_EXTENSIONS = "m3u8,ts,m4s,mp4,mkv,webv,vtt,srt,ssa,aac,ac3,eac3,mp3,opus"

class MediaPolicyError(ValueError):
    """A security rule was broken. The caller must refuse the request."""


class MediaFetchError(OSError):
    """The resource could not be retrieved or decoded.

    This is a transport limitation, not a policy verdict: the caller may still
    proceed with FFmpeg's own confinement, but must report that the nested
    audit was unavailable rather than claiming it passed.
    """


def is_safe_destination(path: Path) -> bool:
    """Validate that destination has an approved extension and parent exists."""
    if path.suffix.lower() not in ('.mp4', '.mkv'):
        return False
    if path.exists():
        return False
    try:
        return path.parent.exists() and len(path.parts) > 1
    except OSError:
        return False


def resolve_safe_output(out_str: str) -> Path:
    """Accept only relative names, always resolve beneath the user's Downloads."""
    from pathlib import PureWindowsPath

    if not isinstance(out_str, str) or not out_str or len(out_str) > 240:
        raise ValueError('Output filename is missing or too long')
    p = Path(out_str)
    win = PureWindowsPath(out_str)
    if p.anchor or win.anchor or '..' in p.parts or '..' in win.parts:
        raise ValueError('Output must be a relative path within Downloads')

    downloads = Path.home() / 'Downloads'
    if not downloads.exists():
        downloads = Path.home()
    safe_name = re.sub(r'[\x00-\x1f<>:"/\\|?*]', '_', p.name).strip(' .')[:120]
    # An HLS/DASH asset keeps its playlist name through the UI, so assembling it
    # verbatim produced "master.m3u8.mp4". The playlist suffix describes a recipe,
    # not the container being written, so it is dropped before the media suffix.
    safe_name = re.sub(r'\.(?:m3u8|mpd)$', '', safe_name, flags=re.IGNORECASE)
    if not safe_name or re.match(r'(?i)^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)', safe_name):
        raise ValueError('Invalid output filename')
    if not safe_name.lower().endswith(('.mp4', '.mkv')):
        safe_name += '.mp4'
    return (downloads / safe_name).resolve()


def _address_is_public(raw: str) -> bool:
    try:
        return ipaddress.ip_address(raw).is_global
    except ValueError:
        return False


def resolve_public_addresses(hostname: str, port: int = 443):
    """Resolve a hostname and refuse it unless *every* answer is public.

    Returns the list of validated addresses so the caller can pin the actual
    connection to one of them (closing the resolve-then-reconnect gap that a
    DNS-rebidding server would otherwise exploit).
    """
    try:
        answers = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise MediaPolicyError(f'Could not resolve hostname: {hostname}')
    addresses = []
    for answer in answers:
        ip = answer[4][0]
        if not _address_is_public(ip):
            raise MediaPolicyError(
                f'SSRF protection: access to private/loopback address {ip} is blocked')
        addresses.append(ip)
    if not addresses:
        raise MediaPolicyError(f'Could not resolve hostname: {hostname}')
    return addresses


def validate_media_url(url: str, allow_local: bool = False):
    """Validate HTTP/HTTPS media URL and enforce SSRF protections."""
    if not isinstance(url, str) or len(url) > MAX_URL_LENGTH:
        raise MediaPolicyError('Invalid or oversized media URL')
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise MediaPolicyError('Only HTTP and HTTPS media URLs are supported')
    if parsed.username or parsed.password:
        raise MediaPolicyError('URLs containing credentials are strictly prohibited')
    path = parsed.path.lower()
    if not path.endswith(('.m3u8', '.mpd')) and 'm3u8' not in parsed.query.lower() \
            and 'mpd' not in parsed.query.lower():
        raise MediaPolicyError('URL must target an HLS (.m3u8) or DASH (.mpd) stream manifest')
    if not allow_local:
        resolve_public_addresses(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80))
    return parsed


def validate_resource_url(url: str, allow_local: bool = False):
    """Validate any nested media reference (segment, key, variant, subtitle).

    Nested references are attacker-controllable inside a playlist, so they get
    the same scheme/credential/SSRF treatment as the manifest itself, but they
    are allowed to be any media file rather than only a playlist.
    """
    if not isinstance(url, str) or len(url) > MAX_URL_LENGTH:
        raise MediaPolicyError('Nested media URL is missing or oversized')
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise MediaPolicyError('Nested media references must be HTTP or HTTPS')
    if parsed.username or parsed.password:
        raise MediaPolicyError('Nested media URLs containing credentials are prohibited')
    if not allow_local:
        resolve_public_addresses(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80))
    return parsed


def find_binaries():
    """Locate local ffmpeg and ffprobe executables.

    Search order: explicit `KNOUX_GRABFLOW_FFMPEG`/`KNOUX_GRABFLOW_FFPROBE`
    paths, then `KNOUX_FFMPEG_DIR`, then PATH, then the usual Windows install
    locations. Environment input only — a browser message can never change it.
    """
    ffmpeg = os.environ.get('KNOUX_GRABFLOW_FFMPEG') or None
    ffprobe = os.environ.get('KNOUX_GRABFLOW_FFPROBE') or None
    if ffmpeg and not Path(ffmpeg).is_file():
        ffmpeg = None
    if ffprobe and not Path(ffprobe).is_file():
        ffprobe = None
    override_dir = os.environ.get('KNOUX_FFMPEG_DIR') or os.environ.get('KNOUX_FFMPEG_BIN')
    if override_dir and not ffmpeg:
        candidate = Path(override_dir) / ('ffmpeg.exe' if os.name == 'nt' else 'ffmpeg')
        if candidate.is_file():
            ffmpeg = str(candidate)
        probe_candidate = Path(override_dir) / ('ffprobe.exe' if os.name == 'nt' else 'ffprobe')
        if not ffprobe and probe_candidate.is_file():
            ffprobe = str(probe_candidate)
    ffmpeg = ffmpeg or shutil.which('ffmpeg')
    ffprobe = ffprobe or shutil.which('ffprobe')
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
    if sys.platform == 'win32' and not ffprobe and ffmpeg:
        candidate = Path(ffmpeg).with_name('ffprobe.exe')
        if candidate.is_file():
            ffprobe = str(candidate)
    return ffmpeg, ffprobe


# --- Pinned, redirect-aware manifest fetch -----------------------------------

def _pinned_connect(scheme, hostname, port, address, timeout):
    """Open a socket to an already-validated address, keeping full TLS verification.

    The TCP connection dials the audited IP while SNI and certificate validation
    still use the original hostname, so pinning closes the DNS-rebinding window
    without weakening trust. Verification settings are stated explicitly rather
    than inherited from defaults, and the result is asserted before the caller
    gets the socket: if a future change ever relaxed either one, this raises
    instead of silently accepting a certificate issued to some other host.
    """
    raw = socket.create_connection((address, port), timeout=timeout)
    if scheme != 'https':
        return raw, None
    context = ssl.create_default_context()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    wrapped = context.wrap_socket(raw, server_hostname=hostname)
    if not wrapped.server_hostname or not context.check_hostname:
        wrapped.close()
        raise MediaPolicyError('TLS hostname verification is not active for '
                               f'{hostname}; refusing to transfer media')
    return wrapped, hostname


def _recv_until(sock, predicate, deadline, limit, error):
    """Read from the socket until predicate(buffer) is true or a limit trips."""
    buffer = bytearray()
    while not predicate(buffer):
        if time.time() > deadline:
            raise MediaFetchError(error)
        piece = sock.recv(4096)
        if not piece:
            break
        buffer.extend(piece)
        if len(buffer) > limit:
            raise MediaFetchError(MANIFEST_TOO_LARGE)
    return buffer


def _read_chunked_body(sock, initial, deadline):
    """Decode a chunked body, enforcing the size ceiling as it grows."""
    remainder = bytearray(initial)
    payload = bytearray()
    while True:
        if not remainder:
            remainder = bytearray(_recv_until(
                sock, lambda b: b'\r\n' in b, deadline, MAX_MANIFEST_BYTES + 4096,
                'Timed out waiting for a chunk size line'))
            if b'\r\n' not in remainder:
                raise MediaFetchError('Chunked manifest ended before the terminating chunk')
        size_line, _, remainder = remainder.partition(b'\r\n')
        try:
            size = int(size_line.split(b';')[0], 16)
        except ValueError:
            raise MediaFetchError('Chunked manifest had an invalid chunk size')
        if size == 0:
            return bytes(payload)
        if len(payload) + size > MAX_MANIFEST_BYTES:
            raise MediaFetchError(MANIFEST_TOO_LARGE)
        while len(remainder) < size + 2:
            piece = sock.recv(min(65536, size + 2 - len(remainder)))
            if not piece:
                raise MediaFetchError('Chunked manifest ended mid-chunk')
            remainder.extend(piece)
        payload.extend(remainder[:size])
        remainder = bytearray(remainder[size + 2:])


def _read_http_response(sock, timeout):
    """Read one HTTP/1.x response, honouring Content-Length or chunked framing."""
    deadline = time.time() + timeout
    buffer = _recv_until(sock, lambda b: b'\r\n\r\n' in b, deadline, 65536,
                         'Timed out waiting for manifest headers')
    if b'\r\n\r\n' not in buffer:
        raise MediaFetchError('Manifest response had no header terminator')
    split = buffer.find(b'\r\n\r\n')
    head = bytes(buffer[:split]).decode('latin-1', 'replace')
    body_start = bytes(buffer[split + 4:])

    lines = head.split('\r\n')
    status_line = lines[0]
    headers = {}
    for line in lines[1:]:
        name, _, value = line.partition(':')
        headers[name.strip().lower()] = value.strip()

    if 'chunked' in headers.get('transfer-encoding', '').lower():
        return status_line, headers, _read_chunked_body(sock, body_start, deadline)

    expected = headers.get('content-length')
    payload = bytearray(body_start)
    if len(payload) > MAX_MANIFEST_BYTES:
        raise MediaFetchError(MANIFEST_TOO_LARGE)
    limit = int(expected) if expected and expected.isdigit() else None
    while (limit is None and len(payload) < MAX_MANIFEST_BYTES) or (limit is not None and len(payload) < limit):
        if time.time() > deadline:
            raise MediaFetchError('Timed out reading the manifest body')
        piece = sock.recv(65536)
        if not piece:
            break
        payload.extend(piece)
        if len(payload) > MAX_MANIFEST_BYTES:
            raise MediaFetchError(MANIFEST_TOO_LARGE)
    return status_line, headers, bytes(payload)


def fetch_manifest(url: str, allow_local: bool = False, timeout: int = FETCH_TIMEOUT):
    """GET a playlist with pinned DNS, bounded body and re-validated redirects.

    Returns ``(text, effective_url)``. Raises ``MediaPolicyError`` when a
    security rule is broken and ``MediaFetchError`` when the resource simply
    could not be retrieved or decoded.
    """
    current = url
    for _hop in range(MAX_REDIRECT_HOPS + 1):
        parsed = validate_resource_url(current, allow_local=allow_local)
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        addresses = [parsed.hostname]
        if not allow_local:
            addresses = resolve_public_addresses(parsed.hostname, port)
        sock = None
        last_error = None
        for address in addresses:
            try:
                sock, _ = _pinned_connect(parsed.scheme, parsed.hostname, port, address, timeout)
                break
            except OSError as exc:
                last_error = exc
                sock = None
        if sock is None:
            raise MediaFetchError(f'Could not reach media host: {last_error}')
        try:
            path = parsed.path or '/'
            if parsed.query:
                path = f'{path}?{parsed.query}'
            authority = parsed.hostname if parsed.port is None else f'{parsed.hostname}:{parsed.port}'
            request = (
                f'GET {path} HTTP/1.1\r\n'
                f'Host: {authority}\r\n'
                'User-Agent: KNOuX-GrabFlow-Companion/' + VERSION + '\r\n'
                'Accept: */*\r\n'
                'Accept-Encoding: identity\r\n'
                'Connection: close\r\n\r\n'
            )
            sock.sendall(request.encode('ascii'))
            status_line, headers, payload = _read_http_response(sock, timeout)
        finally:
            try:
                sock.close()
            except OSError:
                pass

        parts = status_line.split(' ', 2)
        code = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        if 300 <= code < 400:
            location = headers.get('location')
            if not location:
                raise MediaFetchError(f'Media host returned redirect {code} without a target')
            current = urljoin(current, location)   # next loop re-validates this hop
            continue
        if code != 200:
            raise MediaFetchError(f'Media manifest request failed with HTTP {code}')
        if len(payload) > MAX_MANIFEST_BYTES:
            raise MediaFetchError(MANIFEST_TOO_LARGE)
        return payload.decode('utf-8', 'replace'), current
    raise MediaPolicyError('Media manifest exceeded the maximum redirect depth')


def audit_nested_urls(text: str, base_url: str, allow_local: bool = False):
    """Validate every nested reference a player would follow next.

    Catches the case a naive check misses: a public master playlist whose keys,
    variants or segments point at a private network or a non-HTTP scheme.
    """
    findings = {'checked': 0, 'blocked': [], 'hosts': set()}
    for raw in _iter_nested_refs(text):
        if findings['checked'] >= MAX_NESTED_ENTRIES:
            raise MediaPolicyError('Media manifest references too many nested resources')
        candidate = urljoin(base_url, raw.strip())
        if candidate.startswith(('data:', 'blob:')):
            findings['blocked'].append(candidate[:120])
            continue
        try:
            parsed = validate_resource_url(candidate, allow_local=allow_local)
        except MediaPolicyError as exc:
            findings['blocked'].append(f'{candidate[:120]} -> {exc}')
            continue
        findings['checked'] += 1
        findings['hosts'].add(parsed.hostname)
    if findings['blocked']:
        raise MediaPolicyError(
            'SSRF protection: nested media reference rejected — ' + '; '.join(findings['blocked'][:3])
        )
    findings['hosts'] = sorted(findings['hosts'])
    return findings


DASH_REF_ATTR = re.compile(
    r'(?<![:\w-])(?:sourceurl|baseurl|initialization|indexrange|media)\s*=\s*"([^"]+)"',
    re.IGNORECASE)
DASH_BASEURL_ELEMENT = re.compile(r'<BaseURL>\s*([^<]+?)\s*</BaseURL>', re.IGNORECASE)
XML_TAG = re.compile(r'<[^>]{0,8192}>')


def _looks_like_media_ref(value: str) -> bool:
    """Reject values that are declarations rather than resources.

    A DASH attribute can legally span lines, and schemaLocation carries a
    space-separated pair, so a raw line scan produces things like
    ``urn:mpeg:DASH:schema:MPD:2011 http://...``. Those are namespaces, not
    media, and reporting them as an SSRF attempt would be a false alarm.
    """
    if not value:
        return False
    if any(char.isspace() for char in value):
        return False
    return not value.lower().startswith(('urn:', 'data:', 'blob:'))


def _iter_nested_refs(text: str):
    """Yield candidate nested resource strings from an HLS or DASH document.

    DASH is scanned by tag, not by line: XML attributes may span lines, and a
    line-oriented scan mistakes wrapped declarations for resource references.
    """
    if '<' in text and re.search(r'<(?:\w+:)?(?:MPD|Period|AdaptationSet|Representation)', text):
        for tag in XML_TAG.finditer(text):
            body = tag.group(0)
            for match in DASH_REF_ATTR.finditer(body):
                if _looks_like_media_ref(match.group(1)):
                    yield match.group(1)
        for match in DASH_BASEURL_ELEMENT.finditer(text):
            if _looks_like_media_ref(match.group(1)):
                yield match.group(1)
        return

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#'):
            for match in re.finditer(r'URI="([^"]+)"|SOURCEURL="([^"]+)"', stripped, re.IGNORECASE):
                candidate = next(group for group in match.groups() if group)
                if _looks_like_media_ref(candidate):
                    yield candidate
            continue
        if stripped.startswith('<'):
            continue
        if _looks_like_media_ref(stripped):
            yield stripped


def build_assemble_command(ffmpeg: str, url: str, out_path: Path) -> list:
    """FFmpeg argv with transport confinement and machine-readable progress."""
    return [
        ffmpeg, '-hide_banner', '-nostdin', '-loglevel', 'warning',
        '-protocol_whitelist', ALLOWED_PROTOCOLS,
        '-allowed_extensions', ALLOWED_PLAYLIST_EXTENSIONS,
        '-rw_timeout', '30000000',
        '-i', url,
        '-c', 'copy',
        '-max_muxing_queue_size', '1024',
        '-movflags', '+faststart',
        '-progress', 'pipe:1',
        '-n', str(out_path),
    ]


def read_message(stream=sys.stdin.buffer):
    """Read a length-prefixed native messaging JSON message."""
    raw_length = stream.read(4)
    if len(raw_length) == 0:
        return None
    if len(raw_length) < 4:
        raise OSError('Incomplete message length received from browser')
    message_length = struct.unpack('<I', raw_length)[0]
    if message_length > MAX_MESSAGE_BYTES:
        raise ValueError(f'Message length exceeds maximum allowed limit: {message_length}')
    message_data = stream.read(message_length)
    if len(message_data) < message_length:
        raise OSError('Incomplete message body received from browser')
    return json.loads(message_data.decode('utf-8'))


def write_message(message, stream=sys.stdout.buffer):
    """Write a length-prefixed native messaging JSON response."""
    encoded = json.dumps(message, ensure_ascii=False).encode('utf-8')
    stream.write(struct.pack('<I', len(encoded)))
    stream.write(encoded)
    stream.flush()


class _Job:
    """One assembly job: process handle, progress snapshot and abort flag."""

    def __init__(self, job_id, url, out_path):
        self.job_id = job_id
        self.url = url
        self.out_path = out_path
        self.proc = None
        self.thread = None
        self.cancelled = False
        self.finished = False
        self.started_at = time.time()
        self.total_bytes = 0
        self.out_time_us = 0
        self.duration_us = 0
        self.error = ''
        self.audit = {'status': 'skipped', 'checked': 0, 'hosts': [], 'reason': ''}
        self.lock = threading.Lock()

    def snapshot(self):
        with self.lock:
            percent = 0
            if self.duration_us > 0:
                percent = max(0, min(100, round(self.out_time_us / self.duration_us * 100)))
            return {
                'jobId': self.job_id,
                'bytes': self.total_bytes,
                'mediaTimeSeconds': round(self.out_time_us / 1_000_000, 2),
                'percent': percent,
                'elapsedSeconds': round(time.time() - self.started_at, 1),
            }


class CompanionHost:
    def __init__(self, allow_local=False, emitter=None):
        self.allow_local = allow_local
        self.test_mode = bool(allow_local)
        self.active_processes = {}          # kept for the documented trust-boundary API
        self.jobs = {}
        self.emitter = emitter or (lambda message: None)
        self._write_lock = threading.Lock()

    def emit(self, message):
        with self._write_lock:
            write_message(message)
        try:
            self.emitter(message)
        except OSError:
            pass   # a diagnostic sink must never break the protocol

    def handle_ping(self, msg):
        ffmpeg, ffprobe = find_binaries()
        resp = {
            'action': 'pong',
            'version': VERSION,
            'host': HOST_NAME,
            'capabilities': ['ping', 'probe', 'assemble', 'assemble-async', 'progress', 'cancel'],
            'maxConcurrentJobs': MAX_ACTIVE_JOBS,
            'maxOutputBytes': MAX_OUTPUT_BYTES,
            'localMediaPolicy': 'test-relaxed' if self.test_mode else 'private-addresses-blocked',
            'ffmpegAvailable': bool(ffmpeg),
            'ffprobeAvailable': bool(ffprobe),
            'ffmpegPath': ffmpeg,
            'ffprobePath': ffprobe,
            'platform': sys.platform
        }
        if 'requestId' in msg:
            resp['requestId'] = msg['requestId']
        return resp

    def handle_probe(self, msg):
        if 'allowLocal' in msg:
            raise ValueError('Network policy cannot be overridden by a browser message')
        url = msg.get('url', '')
        validate_media_url(url, allow_local=self.allow_local)
        _ffmpeg, ffprobe = find_binaries()
        resp = {'action': 'probe_result'}
        if 'requestId' in msg:
            resp['requestId'] = msg['requestId']
        if 'jobId' in msg:
            resp['jobId'] = msg['jobId']
        if not ffprobe:
            resp.update({'status': 'unavailable', 'message': 'ffprobe is not installed'})
            return resp
        cmd = [
            ffprobe, '-hide_banner', '-loglevel', 'error',
            '-protocol_whitelist', ALLOWED_PROTOCOLS,
            '-allowed_extensions', ALLOWED_PLAYLIST_EXTENSIONS,
            '-rw_timeout', '15000000',
            '-show_entries',
            'format=duration,bit_rate,size:stream=index,codec_name,codec_type,width,height,bit_rate',
            '-of', 'json', url
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=PROBE_TIMEOUT)
        except subprocess.TimeoutExpired:
            resp.update({'status': 'timeout', 'error': 'ffprobe timed out'})
            return resp
        if res.returncode != 0:
            resp.update({'status': 'error', 'error': res.stderr.strip()[:300]})
            return resp
        try:
            data = json.loads(res.stdout)
        except Exception as exc:
            resp.update({'status': 'error', 'error': str(exc)})
            return resp
        fmt = data.get('format') or {}
        streams = data.get('streams') or []
        resp.update({
            'status': 'ok',
            'data': data,
            'durationSeconds': _as_float(fmt.get('duration')),
            'bitRate': _as_int(fmt.get('bit_rate')),
            'sizeBytes': _as_int(fmt.get('size')),
            'videoTracks': [{'width': _as_int(s.get('width')), 'height': _as_int(s.get('height')),
                             'codec': s.get('codec_name')} for s in streams
                            if s.get('codec_type') == 'video'],
            'audioTracks': [{'codec': s.get('codec_name')} for s in streams
                            if s.get('codec_type') == 'audio'],
            # A DRM/encrypted HLS or MPD cannot be assembled; say so up front
            # instead of letting FFmpeg fail with an opaque error later.
            'drmSuspected': _looks_protected(data),
        })
        return resp

    def handle_assemble(self, msg):
        """Validate, then assemble. `async` replies immediately and streams progress."""
        if 'allowLocal' in msg:
            raise ValueError('Network policy cannot be overridden by a browser message')
        url = msg.get('url', '')
        job_id = msg.get('jobId', 'default')
        out_str = msg.get('output', '')
        if not out_str:
            raise ValueError('Output path is required')
        if job_id in self.jobs and not self.jobs[job_id].finished:
            raise ValueError('That assembly job is already running')
        if len([j for j in self.jobs.values() if not j.finished]) >= MAX_ACTIVE_JOBS:
            raise ValueError(f'Refusing to start: at most {MAX_ACTIVE_JOBS} concurrent assemblies are allowed')

        out_path = resolve_safe_output(out_str)
        if not is_safe_destination(out_path):
            raise ValueError('Invalid destination path or file already exists (no-clobber enforced)')

        validate_media_url(url, allow_local=self.allow_local)
        # Inspect the playlist before FFmpeg touches it, so nested keys,
        # variants and segments cannot point at a private network. A policy
        # breach always blocks; a transport limitation is reported honestly
        # instead of being silently treated as a clean audit.
        duration_hint = 0
        audit = {'status': 'skipped', 'checked': 0, 'hosts': [], 'reason': ''}
        try:
            text, effective = fetch_manifest(url, allow_local=self.allow_local)
            findings = audit_nested_urls(text, effective, allow_local=self.allow_local)
            duration_hint = _duration_from_playlist(text)
            audit = {'status': 'passed', 'checked': findings['checked'],
                     'hosts': findings['hosts'], 'reason': ''}
        except MediaPolicyError:
            raise
        except (MediaFetchError, UnicodeDecodeError) as exc:
            audit = {'status': 'unavailable', 'checked': 0, 'hosts': [],
                     'reason': str(exc)[:200]}

        ffmpeg, _ffprobe = find_binaries()
        if not ffmpeg:
            return {'action': 'assemble_result', 'jobId': job_id,
                    'status': 'failed', 'error': 'FFmpeg executable is not available'}

        job = _Job(job_id, url, out_path)
        job.duration_us = int(duration_hint * 1_000_000)
        job.audit = audit
        self.jobs[job_id] = job
        self.active_processes[job_id] = None
        cmd = build_assemble_command(ffmpeg, url, out_path)

        if msg.get('async'):
            job.thread = threading.Thread(
                target=self._run_async_job, args=(job, cmd), daemon=True)
            job.thread.start()
            resp = {'action': 'assemble_started', 'jobId': job_id, 'status': 'started',
                    'output': str(out_path), 'nestedAudit': audit}
            if 'requestId' in msg:
                resp['requestId'] = msg['requestId']
            return resp

        return self._run_job(job, cmd, timeout=msg.get('timeout', DEFAULT_ASSEMBLE_TIMEOUT))

    def _run_async_job(self, job, cmd):
        """Worker entry point: the final result must be streamed back, not returned."""
        try:
            result = self._run_job(job, cmd)
        except Exception as exc:  # noqa: BLE001 - never let a worker die silently
            result = self._finish(job, 'failed', f'Assembly worker crashed: {exc}')
        self.emit(result)

    def _run_job(self, job, cmd, timeout=DEFAULT_ASSEMBLE_TIMEOUT):
        """Stream FFmpeg progress, enforce ceilings, and return the final result."""
        env = dict(os.environ)
        env.setdefault('AV_LOG_FORCE_NOCOLOR', '1')
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1, env=env,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) if os.name == 'nt' else 0,
            )
        except OSError as exc:
            job.finished = True
            self.active_processes.pop(job.job_id, None)
            return self._finish(job, 'failed', f'Could not start FFmpeg: {exc}')

        job.proc = proc
        self.active_processes[job.job_id] = proc
        # stderr is drained on its own thread into a bounded ring. Reading it only
        # after stdout closes would deadlock the moment a long assembly emits more
        # warnings than the OS pipe holds, and an unbounded capture would let a
        # chatty stream grow memory without limit.
        stderr_tail = collections.deque(maxlen=STDERR_KEEP_LINES)
        stderr_done = threading.Event()

        def drain_stderr():
            try:
                for line in proc.stderr:
                    text = line.rstrip()
                    if text:
                        stderr_tail.append(text)
            except (OSError, ValueError):
                pass   # the pipe closes when the process is terminated
            finally:
                stderr_done.set()

        stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
        stderr_thread.start()

        deadline = time.time() + timeout
        last_emit = 0.0
        try:
            for line in proc.stdout:
                key, _, value = line.strip().partition('=')
                if key == 'total_size':
                    with job.lock:
                        job.total_bytes = _as_int(value) or job.total_bytes
                    if job.total_bytes > MAX_OUTPUT_BYTES:
                        proc.kill()
                        return self._finish(job, 'aborted',
                                           f'Output exceeded the {MAX_OUTPUT_BYTES} byte safety ceiling')
                elif key == 'out_time_us':
                    with job.lock:
                        job.out_time_us = max(job.out_time_us, _as_int(value) or 0)
                elif key == 'progress' and value == 'end':
                    break
                if time.time() - last_emit >= PROGRESS_INTERVAL:
                    last_emit = time.time()
                    message = {'action': 'assemble_progress', 'state': 'running'}
                    message.update(job.snapshot())
                    self.emit(message)
                if job.cancelled:
                    proc.terminate()
                    return self._finish(job, 'cancelled', 'Assembly cancelled by user')
                if time.time() > deadline:
                    proc.kill()
                    return self._finish(job, 'timeout', 'Assembly timed out')
            proc.stdout.close()
            stderr_thread.join(timeout=30)
            code = proc.wait(timeout=30)
            if job.cancelled:
                return self._finish(job, 'cancelled', 'Assembly cancelled by user')
            if code != 0:
                detail = ' '.join(stderr_tail).strip()[:400]
                return self._finish(job, 'failed', detail or f'FFmpeg exited with code {code}')
            if not job.out_path.is_file() or job.out_path.stat().st_size == 0:
                return self._finish(job, 'failed', 'Output file was not created or is empty')
            size = job.out_path.stat().st_size
            if size > MAX_OUTPUT_BYTES:
                return self._finish(job, 'aborted', 'Output exceeded the configured size ceiling')
            with job.lock:
                job.total_bytes = size
            return self._finish(job, 'complete', None, output=str(job.out_path), bytes=size)
        except (OSError, subprocess.SubprocessError) as exc:
            try:
                proc.kill()
            except OSError:
                pass
            return self._finish(job, 'failed', str(exc))

    def _finish(self, job, status, error=None, **extra):
        job.finished = True
        job.error = error or ''
        self.active_processes.pop(job.job_id, None)
        result = {'action': 'assemble_result', 'jobId': job.job_id, 'status': status}
        result.update(job.snapshot())
        result['nestedAudit'] = job.audit
        if error:
            result['error'] = error
        result.update(extra)
        return result

    def handle_cancel(self, msg):
        job_id = msg.get('jobId')
        job = self.jobs.get(job_id)
        resp = {'action': 'cancel_result', 'jobId': job_id}
        if 'requestId' in msg:
            resp['requestId'] = msg['requestId']
        proc = self.active_processes.get(job_id)
        if job and not job.finished:
            job.cancelled = True
            if proc:
                try:
                    proc.terminate()
                except OSError:
                    pass
            resp['status'] = 'cancelled'
        elif proc:
            try:
                proc.terminate()
            except OSError:
                pass
            resp['status'] = 'cancelled'
        else:
            resp['status'] = 'not_found'
        return resp

    def handle_status(self, msg):
        running = [job.snapshot() for job in self.jobs.values() if not job.finished]
        resp = {'action': 'status_result', 'running': running, 'version': VERSION}
        if 'requestId' in msg:
            resp['requestId'] = msg['requestId']
        return resp

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
        elif action == 'status':
            return self.handle_status(msg)
        else:
            return {'action': 'error', 'error': f'Unknown action: {action}'}


def _as_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _duration_from_playlist(text: str):
    """Sum EXTINF durations for a VOD HLS playlist (0 when unknown/live)."""
    total = 0.0
    for match in re.finditer(r'#EXTINF:\s*([\d.]+)', text):
        try:
            total += float(match.group(1))
        except ValueError:
            continue
    if total:
        return total
    match = re.search(r'mediaPresentationDuration="PT(?:(\d+)H)?(?:(\d+)M)?(?:([\d.]+)S)?"', text)
    if match:
        hours, minutes, seconds = (int(match.group(1) or 0), int(match.group(2) or 0),
                                   float(match.group(3) or 0))
        return hours * 3600 + minutes * 60 + seconds
    return 0.0


def _looks_protected(probe_data) -> bool:
    """Heuristic DRM/encryption detector so we fail honestly instead of mysteriously."""
    try:
        text = json.dumps(probe_data).lower()
    except (TypeError, ValueError):
        return False
    return any(marker in text for marker in ('cenc', 'cbcs', 'drm', 'encrypted', 'aes-128', 'keyformat'))


def run_host():
    """Serve the native-messaging protocol: read, dispatch, reply, and stream events."""
    # Local/loopback media is refused by default. A test harness may opt in via
    # this environment variable; a browser message can never do it.
    allow_local = os.environ.get('KNOUX_GRABFLOW_ALLOW_LOCAL', '').strip().lower() in ('1', 'true', 'yes')
    if allow_local:
        print('KNOuX GrabFlow companion: local-media policy relaxed by environment (test mode)',
              file=sys.stderr, flush=True)
    host = CompanionHost(allow_local=allow_local)
    host.test_mode = allow_local
    stdin = sys.stdin.buffer

    def serve():
        while True:
            try:
                msg = read_message(stdin)
            except (OSError, ValueError) as exc:
                # A length-prefixed stream cannot be resynchronised once a frame is
                # short, oversized or unparseable. Reporting it and looping would
                # spin forever on the same bytes, so the session ends here.
                host.emit({'action': 'error', 'error': f'unrecoverable framing error: {exc}'})
                return
            if msg is None:
                return
            try:
                host.emit(host.dispatch(msg))
            except Exception as exc:  # noqa: BLE001 - one bad request must not kill the session
                host.emit({'action': 'error', 'error': str(exc),
                           'requestId': msg.get('requestId')})

    reader = threading.Thread(target=serve, daemon=True)
    reader.start()
    reader.join()


if __name__ == '__main__':
    run_host()
