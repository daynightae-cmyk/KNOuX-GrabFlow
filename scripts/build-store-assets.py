#!/usr/bin/env python3
"""Build genuine browser screenshots and KNOuX-branded store promo graphics.

The popup imagery MUST originate from the verified real-MV3 test. Each
1280x800 store screenshot uses an unmodified crop of that real capture on a
branded backdrop with descriptive text; no popup UI is simulated or drawn.
Promotional art uses the repository's existing KNOuX stag SVG.

Usage:
    python scripts/build-store-assets.py
    python scripts/build-store-assets.py --screenshots screenshots \
        --output store-assets/0.6.7

The environment variables GRABFLOW_E2E_SCREENSHOT_DIR and
KNOUX_GRABFLOW_STORE_ASSETS_DIR remain supported for the existing CI/release
pipeline. Existing branded files are regenerated deterministically; the icon
copy is never replaced with different bytes.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import os
import shutil
import struct
import tempfile

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_VERSION = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))["version"]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--screenshots",
        default=os.environ.get("GRABFLOW_E2E_SCREENSHOT_DIR", str(ROOT / "screenshots")),
        help="Directory containing the real 1280x800 MV3 screenshots.",
    )
    parser.add_argument(
        "--output",
        default=os.environ.get(
            "KNOUX_GRABFLOW_STORE_ASSETS_DIR", str(ROOT / "store-assets" / MANIFEST_VERSION)
        ),
        help="Directory for the generated store assets.",
    )
    parser.add_argument(
        "--version",
        default=MANIFEST_VERSION,
        help="Version label used in generated filenames (default: manifest version).",
    )
    return parser.parse_args()


def dims(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not PNG " + str(path))
    return struct.unpack(">II", data[16:24])


def copy_unchanged(source, target):
    """Copy source to target, but never replace different existing bytes."""
    assert source.is_file(), source
    if target.exists():
        assert target.read_bytes() == source.read_bytes(), f"Existing asset differs: {target}"
    else:
        shutil.copy2(source, target)


def write_unchanged(target, data):
    """Write bytes only when the target is missing or already identical."""
    if target.exists():
        assert target.read_bytes() == data, f"Existing generated asset differs: {target}"
    else:
        target.write_bytes(data)


def render_unchanged(page, html, target, size, label):
    """Render off to the side, then copy only if the target is absent/identical."""
    descriptor, temporary = tempfile.mkstemp(prefix="knoux-store-", suffix=".png")
    os.close(descriptor)
    staged = Path(temporary)
    try:
        page.set_content(html, wait_until="load")
        page.screenshot(path=str(staged))
        assert dims(staged) == size, (staged, dims(staged))
        copy_unchanged(staged, target)
        print(label, target, dims(target))
    finally:
        staged.unlink(missing_ok=True)


def showcase_html(layout, capture_path, svg):
    x, y, w, h = layout["crop"]
    scale = 1.1
    frame_w = round(w * scale)
    frame_h = round(h * scale)
    source_w = round(1280 * scale)
    source_h = round(800 * scale)
    rtl = layout["lang"] == "ar"
    direction = "rtl" if rtl else "ltr"
    card_left = 1280 - 64 - frame_w if rtl else 64
    copy_left = 64 if rtl else 620
    bullets = "".join(
        f"<li><span class='tick'>&#10003;</span><span>{item}</span></li>"
        for item in layout["bullets"]
    )
    encoded = base64.b64encode(capture_path.read_bytes()).decode("ascii")
    body_class = ' class="rtl"' if rtl else ""
    return f"""<!DOCTYPE html><html lang="{layout['lang']}" dir="{direction}"><head><meta charset="utf-8">
<style>
* {{box-sizing:border-box}}
html,body{{width:100%;height:100%;margin:0;overflow:hidden}}
body{{font-family:'Segoe UI',Tahoma,Arial,sans-serif;color:#f5f2ff;
background:
radial-gradient(ellipse at 76% 38%,rgba(124,58,237,.30),transparent 55%),
radial-gradient(ellipse at 16% 82%,rgba(192,132,252,.13),transparent 52%),
linear-gradient(135deg,#080512 0%,#0d0817 52%,#170f26 100%)}}
.glow{{position:absolute;width:680px;height:680px;left:-160px;top:70px;
background:radial-gradient(circle,rgba(124,58,237,.32),transparent 66%);filter:blur(34px)}}
body.rtl .glow{{left:auto;right:-160px}}
.card{{position:absolute;top:59px;left:{card_left}px;width:{frame_w}px;height:{frame_h}px;
overflow:hidden;border-radius:20px;background:#06060f;
border:1px solid rgba(192,132,252,.36);
box-shadow:0 34px 90px rgba(0,0,0,.70),0 0 0 1px rgba(255,255,255,.03),0 0 70px rgba(124,58,237,.20)}}
.card img{{display:block;width:{source_w}px;height:{source_h}px;
margin-left:-{round(x * scale)}px;margin-top:-{round(y * scale)}px}}
.copy{{position:absolute;top:50%;left:{copy_left}px;width:596px;transform:translateY(-50%);
direction:{direction};text-align:{'right' if rtl else 'left'}}}
.brand{{display:flex;align-items:center;gap:13px;margin-bottom:26px;
color:#cfc3e4;font-size:12px;font-weight:800;letter-spacing:.22em;text-transform:uppercase}}
.brand svg{{width:42px;height:42px;filter:drop-shadow(0 0 14px rgba(192,132,252,.50))}}
.title{{font-size:{48 if rtl else 54}px;line-height:{1.28 if rtl else 1.07};
letter-spacing:-.01em;font-weight:900;margin:0}}
.title em{{color:#c084fc;font-style:normal}}
.body{{margin:23px 0 0;font-size:{18 if rtl else 19}px;line-height:1.58;color:#c9bfda;max-width:560px}}
ul{{list-style:none;padding:0;margin:30px 0 0}}
li{{display:flex;align-items:center;gap:13px;margin:0 0 14px;font-size:17px;color:#ece6f7}}
body.rtl .copy li{{flex-direction:row-reverse}}
.tick{{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;
width:24px;height:24px;border-radius:50%;background:rgba(192,132,252,.16);
border:1px solid rgba(192,132,252,.48);color:#d8b4fe;font-size:13px;font-weight:900}}
.footnote{{position:absolute;bottom:44px;left:{copy_left}px;width:596px;
direction:{direction};text-align:{'right' if rtl else 'left'};
font-size:10px;font-weight:700;letter-spacing:{'.05em' if rtl else '.19em'};
text-transform:uppercase;color:#877a9e}}
</style></head><body{body_class}>
<div class="glow"></div>
<div class="card"><img alt="Real KNOuX GrabFlow popup capture" src="data:image/png;base64,{encoded}"></div>
<div class="copy">
<div class="brand">{svg}<span>KNOuX LABS</span></div>
<div class="title">{layout['title']}</div>
<div class="body">{layout['body']}</div>
<ul>{bullets}</ul>
</div>
<div class="footnote">{layout['footnote']}</div>
</body></html>"""


def promo_html(w, h, svg):
    wordsize = 35 if w == 440 else 90
    icon = 117 if w == 440 else 290
    subtitle = 13 if w == 440 else 30
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
* {{box-sizing:border-box}}
html,body{{width:100%;height:100%;margin:0;overflow:hidden;background:#080512}}
body{{font-family:'Segoe UI',Arial,sans-serif;color:#f5f2ff}}
.stage{{height:100%;width:100%;background:
radial-gradient(ellipse at 65% 45%,rgba(124,58,237,.40),transparent 50%),
radial-gradient(ellipse at 20% 80%,rgba(192,132,252,.21),transparent 55%),
linear-gradient(128deg,#080512 7%,#130d22 58%,#211438 100%);
position:relative;display:flex;align-items:center;justify-content:space-around}}
.stage:before{{content:'';position:absolute;inset:5%;border:1px solid rgba(192,132,252,.28);border-radius:20px}}
.light{{position:absolute;width:65%;height:110%;right:-15%;background:radial-gradient(ellipse,rgba(124,58,237,.24),transparent 72%);filter:blur(6px)}}
.logo{{z-index:1;display:flex;align-items:center;justify-content:center;width:{icon}px;height:{icon}px;filter:drop-shadow(0 0 27px rgba(192,132,252,.58))}}
.logo svg{{width:100%;height:100%}}
.copy{{position:relative;z-index:1;text-align:left;max-width:60%}}
.name{{font-size:{wordsize}px;letter-spacing:.01em;font-weight:900;line-height:1.05}}
.name strong{{color:#c084fc;font-weight:900}}
.subtitle{{margin-top:14px;font-size:{subtitle}px;letter-spacing:0.11em;color:#e0caff;font-weight:650}}
.line{{width:43%;height:3px;background:linear-gradient(90deg,#c084fc,transparent);margin-top:17px}}
</style></head><body>
<div class="stage"><div class="light"></div><div class="logo">{svg}</div>
<div class="copy"><div class="name">KNOuX<br><strong>GRABFLOW</strong></div>
<div class="subtitle">VIDEO &middot; AUDIO &middot; STREAMS</div><div class="line"></div>
</div></div></body></html>"""


def logo_html(svg):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
* {{box-sizing:border-box}}
html,body{{width:100%;height:100%;margin:0;overflow:hidden;background:#080512}}
body{{font-family:'Segoe UI',Arial,sans-serif}}
.stage{{height:100%;width:100%;background:
radial-gradient(ellipse at 50% 42%,rgba(124,58,237,.46),transparent 58%),
linear-gradient(145deg,#080512 10%,#160e28 60%,#211438 100%);
display:flex;align-items:center;justify-content:center;position:relative}}
.stage:before{{content:'';position:absolute;inset:7%;border:2px solid rgba(192,132,252,.30);border-radius:52px}}
.logo{{position:relative;z-index:1;width:230px;height:230px;filter:drop-shadow(0 0 34px rgba(192,132,252,.62))}}
.logo svg{{width:100%;height:100%}}
</style></head><body>
<div class="stage"><div class="logo">{svg}</div></div></body></html>"""


def main():
    args = parse_args()
    qa = Path(args.screenshots).resolve()
    output = Path(args.output).resolve()
    version = args.version
    assert qa != output
    assert qa.is_dir(), qa
    output.mkdir(parents=True, exist_ok=True)

    # The three source captures are real 1280x800 unpacked-MV3 screenshots.
    # The popup occupies exactly 440x620 at the left or right edge; the rest of
    # the capture is the page background. Cropping those pixels and placing the
    # unchanged image on a branded backdrop keeps the UI genuine while removing
    # dead space from the store image.
    screens = {
        "real-mv3-popup.png": {
            "destination": f"GrabFlow-v{version}-English-1280x800.png",
            "crop": (0, 0, 440, 620),
            "lang": "en",
            "title": "Every asset.<br><em>One click.</em>",
            "body": "GrabFlow scans only the active tab, on demand, and lists direct video, "
                    "HLS/DASH references, audio, images and documents in one video-first view.",
            "bullets": [
                "Video-first discovery",
                "Search, filter and export",
                "Local, private downloads",
            ],
            "footnote": f"REAL UNPACKED MV3 CAPTURE &middot; v{version}",
        },
        "real-mv3-ar-rtl.png": {
            "destination": f"GrabFlow-v{version}-Arabic-RTL-1280x800.png",
            "crop": (840, 0, 440, 620),
            "lang": "ar",
            "title": "كل الوسائط.<br><em>بنقرة واحدة.</em>",
            "body": "يفحص GrabFlow التبويب النشط فقط وعند الطلب، ويعرض الفيديو المباشر "
                    "ومراجع HLS/DASH والصوت والصور والمستندات في عرض واحد يركّز على الفيديو.",
            "bullets": [
                "اكتشاف يركّز على الفيديو",
                "بحث وتصفية وتصدير",
                "تنزيلات محلية وخاصة",
            ],
            "footnote": f"لقطة حقيقية من MV3 &middot; v{version}",
        },
        "real-mv3-download-complete.png": {
            "destination": f"GrabFlow-v{version}-Direct-Video-1280x800.png",
            "crop": (0, 0, 440, 620),
            "lang": "en",
            "title": "Downloads,<br><em>verified.</em>",
            "body": "GrabFlow follows the browser's real download state and reports progress, "
                    "completion and errors. This capture shows a completed MP4 checked "
                    "byte-for-byte and with FFprobe.",
            "bullets": [
                "Real browser download state",
                "Byte-verified local files",
                "No fake completion",
            ],
            "footnote": f"REAL UNPACKED MV3 CAPTURE &middot; v{version}",
        },
    }
    for name, layout in screens.items():
        source = qa / name
        assert source.is_file(), source
        assert dims(source) == (1280, 800), (source, dims(source))
        x, y, w, h = layout["crop"]
        assert (w, h) == (440, 620), layout["crop"]
        assert 0 <= x <= 1280 - w and 0 <= y <= 800 - h, layout["crop"]

    icon_source = ROOT / "icons" / "icon128.png"
    assert icon_source.is_file(), icon_source
    assert dims(icon_source) == (128, 128), dims(icon_source)
    icon_target = output / f"GrabFlow-v{version}-Icon-128x128.png"
    copy_unchanged(icon_source, icon_target)
    print("STORE_ICON", icon_target, dims(icon_target))

    svg = (ROOT / "icons" / "stag.svg").read_text(encoding="utf-8")
    assert "<svg" in svg and "<script" not in svg.lower()
    svg = svg.replace("<svg ", '<svg aria-label="KNOuX stag brand emblem" ')

    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        try:
            for name, layout in screens.items():
                target = output / layout["destination"]
                page = browser.new_page(
                    viewport={"width": 1280, "height": 800}, device_scale_factor=1
                )
                render_unchanged(
                    page, showcase_html(layout, qa / name, svg), target,
                    (1280, 800), "REAL_CAPTURE_COMPOSITE",
                )
                page.close()

            for w, h, name in (
                (440, 280, f"GrabFlow-v{version}-Promo-440x280.png"),
                (1400, 560, f"GrabFlow-v{version}-Marquee-1400x560.png"),
            ):
                page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
                render_unchanged(page, promo_html(w, h, svg), output / name, (w, h), "BRANDED_PROMO")
                page.close()

            page = browser.new_page(viewport={"width": 300, "height": 300}, device_scale_factor=1)
            logo_name = f"GrabFlow-v{version}-Logo-300x300.png"
            render_unchanged(page, logo_html(svg), output / logo_name, (300, 300), "BRANDED_LOGO")
            page.close()
        finally:
            browser.close()

    expected = {layout["destination"] for layout in screens.values()} | {
        f"GrabFlow-v{version}-Promo-440x280.png",
        f"GrabFlow-v{version}-Marquee-1400x560.png",
        f"GrabFlow-v{version}-Logo-300x300.png",
        f"GrabFlow-v{version}-Icon-128x128.png",
    }
    unexpected = sorted({p.name for p in output.glob("*.png")} - expected)
    assert not unexpected, f"Unexpected PNGs in the store-assets directory: {unexpected}"

    manifest = {
        name: {
            "width": dims(output / name)[0],
            "height": dims(output / name)[1],
            "bytes": (output / name).stat().st_size,
            "sha256": hashlib.sha256((output / name).read_bytes()).hexdigest(),
        }
        for name in sorted(expected)
    }
    write_unchanged(
        output / "ASSET_SHA256.json",
        (json.dumps(manifest, indent=2) + "\n").encode("utf-8"),
    )
    print("STORE_ASSETS_VERIFIED", len(manifest), output)


if __name__ == "__main__":
    main()
