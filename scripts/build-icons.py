#!/usr/bin/env python3
"""Derive the extension icon set from the supplied KNOuX GrabFlow orb logo.

The result is committed to icons/ so packaging never depends on this script
running in CI. It exists so the shipped icons are reproducible from a named
source file rather than hand-placed binaries.

Cut-out method: the orb is a disc on a flat background, so the mask is a
feathered circle fitted to the non-background extent. A luminance key alone
would punch holes through the logo's own specular highlights, and that is
exactly what this avoids.

Requires Pillow. Without it the script reports SKIP and changes nothing.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "brand" / "logo-orb-source.png"
OUT = ROOT / "icons"
SIZES = (16, 32, 48, 128)

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    print("SKIP: Pillow is not installed; icons/ already contains committed assets")
    sys.exit(0)

if not SOURCE.is_file():
    sys.exit(f"Missing brand source: {SOURCE}")


def background_extent(image, tolerance=24):
    """Bounding box of pixels that differ from the corner background colour."""
    rgb = image.convert("RGB")
    px = rgb.load()
    width, height = rgb.size
    bg = px[0, 0]
    min_x, min_y, max_x, max_y = width, height, -1, -1
    step = max(1, width // 400)
    for y in range(0, height, step):
        for x in range(0, width, step):
            r, g, b = px[x, y]
            if abs(r - bg[0]) > tolerance or abs(g - bg[1]) > tolerance or abs(b - bg[2]) > tolerance:
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
    if max_x < 0:
        raise SystemExit("Could not separate the logo from its background")
    return min_x, min_y, max_x, max_y


def disc_mask(size, radius, feather):
    """Anti-aliased circular alpha centred in an size x size canvas."""
    scale = 4
    big = Image.new("L", (size * scale, size * scale), 0)
    draw = ImageDraw.Draw(big)
    r = radius * scale
    c = size * scale / 2
    draw.ellipse([c - r, c - r, c + r, c + r], fill=255)
    if feather > 0:
        big = big.filter(ImageFilter.GaussianBlur(feather * scale))
    return big.resize((size, size), Image.LANCZOS)


def render(size, source, centre, radius, pad_ratio=0.045):
    box = int(radius * 2 * (1 + pad_ratio))
    cropped = source.crop((int(centre[0] - box / 2), int(centre[1] - box / 2),
                           int(centre[0] + box / 2), int(centre[1] + box / 2)))
    cropped = cropped.resize((size, size), Image.LANCZOS)
    scale = size / box
    mask = disc_mask(size, radius * scale, max(0.6, size / 128))
    icon = cropped.convert("RGBA")
    icon.putalpha(mask)

    if size <= 48:
        # A dark backing keeps the mark legible on a light browser toolbar,
        # where the thin outer glow of the orb otherwise disappears.
        backing = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        bdraw = ImageDraw.Draw(backing)
        bdraw.ellipse([size * 0.06, size * 0.06, size * 0.94, size * 0.94],
                      fill=(6, 8, 26, 235))
        backing = backing.filter(ImageFilter.GaussianBlur(max(0.4, size / 96)))
        backing.alpha_composite(icon)
        icon = backing
    return icon


def main():
    source = Image.open(SOURCE).convert("RGBA")
    left, top, right, bottom = background_extent(source)
    centre = ((left + right) / 2, (top + bottom) / 2)
    radius = max(right - left, bottom - top) / 2
    print(f"SOURCE {source.size} disc centre=({centre[0]:.0f},{centre[1]:.0f}) radius={radius:.0f}")

    OUT.mkdir(exist_ok=True)
    for size in SIZES:
        icon = render(size, source, centre, radius)
        path = OUT / f"icon{size}.png"
        icon.save(path, "PNG", optimize=True)
        print(f"WROTE {path.name} {icon.size[0]}x{icon.size[1]} "
              f"{path.stat().st_size} bytes")

    # A square marketing tile at store resolution, kept out of the extension zip.
    tile = render(512, source, centre, radius)
    tile_path = ROOT / "brand" / "icon512.png"
    tile.save(tile_path, "PNG", optimize=True)
    print(f"WROTE brand/{tile_path.name} {tile.size[0]}x{tile.size[1]} "
          f"{tile_path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
