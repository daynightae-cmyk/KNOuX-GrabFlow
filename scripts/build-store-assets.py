#!/usr/bin/env python3
"""Build genuine browser screenshots and KNOuX-branded store promo graphics.

Actual screenshots MUST originate from the verified real-MV3 test, not
reconstructed content or a fake app mockup. Promotional art uses the
repository's existing KNOuX stag SVG.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import struct

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
qa = Path(os.environ["GRABFLOW_E2E_SCREENSHOT_DIR"]).resolve()
output = Path(os.environ["KNOUX_GRABFLOW_STORE_ASSETS_DIR"]).resolve()
output.mkdir(parents=True, exist_ok=True)
assert qa != output

def dims(p):
    data = p.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not PNG " + str(p))
    return struct.unpack(">II", data[16:24])

screens = {
    "real-mv3-popup-0.6.1.png": "GrabFlow-English-1280x800.png",
    "real-mv3-ar-rtl.png": "GrabFlow-Arabic-1280x800.png",
    "real-mv3-download-complete.png": "GrabFlow-Direct-Video-1280x800.png",
}
for name, destination in screens.items():
    source = qa / name
    target = output / destination
    assert source.is_file(), source
    assert dims(source) == (1280, 800), (source, dims(source))
    if target.exists():
        assert target.read_bytes() == source.read_bytes(), f"Existing screenshot differs: {target}"
    else:
        shutil.copy2(source, target)
    print("ACTUAL_CHROME_SCREENSHOT", target, dims(target))

svg = (ROOT / "icons" / "stag.svg").read_text(encoding="utf-8")
assert "<svg" in svg and "<script" not in svg.lower()
svg = svg.replace("<svg ", '<svg aria-label="KNOuX stag brand emblem" ')
def promo_html(w,h):
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
<div class="subtitle">VIDEO · AUDIO · STREAMS</div><div class="line"></div>
</div></div></body></html>"""
with sync_playwright() as play:
    browser = play.chromium.launch(headless=True)
    try:
        for w,h,name in ((440,280,"GrabFlow-Promo-440x280.png"),(1400,560,"GrabFlow-Marquee-1400x560.png")):
            page = browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
            page.set_content(promo_html(w,h),wait_until="load")
            page.screenshot(path=str(output/name))
            assert dims(output/name) == (w,h)
            print("BRANDED_PROMO",output/name,dims(output/name))
            page.close()
    finally:
        browser.close()

files = list(output.glob("*.png"))
manifest = {
    f.name:{"width":dims(f)[0],"height":dims(f)[1],"bytes":f.stat().st_size,
            "sha256":hashlib.sha256(f.read_bytes()).hexdigest()}
    for f in sorted(files)
}
(output/"ASSET_SHA256.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
print("STORE_ASSETS_VERIFIED",len(manifest))
