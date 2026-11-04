#!/usr/bin/env python3
"""Resolve FFmpeg/FFprobe for the test suite.

CI installs FFmpeg system-wide, so PATH lookup is enough there. Locally, a
portable build is common and Windows PATH entries from non-native shells do
not always resolve through shutil.which. These variables let a contributor
point the suite at a real FFmpeg and still get a real result:

    KNOUX_FFMPEG_EXE   absolute path to ffmpeg
    KNOUX_FFPROBE_EXE  absolute path to ffprobe
    KNOUX_FFMPEG_DIR   directory containing both

When nothing is found the caller must skip and say so; it may not substitute a
fixture, a mock, or a "pass" for a conversion it did not perform.
"""
import os
from pathlib import Path
import shutil


def _candidate(name):
    explicit = os.environ.get(f"KNOUX_{name.upper()}_EXE", "").strip()
    if explicit and Path(explicit).is_file():
        return explicit
    directory = os.environ.get("KNOUX_FFMPEG_DIR", "").strip()
    if directory:
        for suffix in (".exe", ""):
            path = Path(directory) / f"{name}{suffix}"
            if path.is_file():
                return str(path)
    return shutil.which(name)


def ffmpeg():
    return _candidate("ffmpeg")


def ffprobe():
    return _candidate("ffprobe")


def pair():
    """Return (ffmpeg, ffprobe) or (None, None) when the toolchain is absent."""
    tools = ffmpeg(), ffprobe()
    return tools if all(tools) else (None, None)
