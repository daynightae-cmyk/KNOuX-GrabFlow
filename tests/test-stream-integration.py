"""Local-only functional HLS-to-MP4 test. Requires ffmpeg/ffprobe; skips if absent."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import functools, json, shutil, subprocess, sys, tempfile, threading
from unittest import SkipTest

ROOT=Path(__file__).resolve().parents[1]
if not (shutil.which('ffmpeg') and shutil.which('ffprobe')):
    print('SKIP: FFmpeg/FFprobe missing; no real stream conversion claim')
    sys.exit(0)
with tempfile.TemporaryDirectory(prefix='grabflow-stream-') as d:
    root=Path(d)
    fixtures=root/'fixtures'
    fixtures.mkdir()
    sample=fixtures/'master.m3u8'
    generation=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi',
       '-i','testsrc2=size=160x90:rate=12','-f','lavfi','-i','sine=frequency=440:sample_rate=44100',
       '-t','3','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-c:a','aac',
       '-f','hls','-hls_time','1','-hls_playlist_type','vod',str(sample)],capture_output=True,text=True)
    if generation.returncode:
        raise RuntimeError(f'Could not generate fixture: {generation.stderr}')
    server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(SimpleHTTPRequestHandler,directory=str(fixtures)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        output=root/'assembled.mp4'
        cmd=[sys.executable,str(ROOT/'scripts/assemble_stream.py'),'--url',f'http://127.0.0.1:{server.server_port}/master.m3u8','--output',str(output),'--allow-local']
        completed=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        assert completed.returncode==0, (completed.stderr,completed.stdout)
        assert output.is_file() and output.stat().st_size > 5000
        probe=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type',
                              '-of','json',str(output)],capture_output=True,text=True,check=True)
        media=json.loads(probe.stdout)
        assert 2.5<float(media['format']['duration'])<4.0,media
        assert {'video','audio'}.issubset({s['codec_type'] for s in media['streams']}),media
        print('PASS real unencrypted HLS => playable MP4: video + audio, approx 3 seconds, bytes',output.stat().st_size)
    finally: server.shutdown();server.server_close()
