"""
V3.1 Image processor — fast, professional bead-art blueprint generation.

Key optimisation: use Pillow's C-level quantize() to reduce the pre-resized
image to ≤256 palette entries, then map only the *palette* (not every pixel)
to bead colours via Lab KD-tree. This cuts runtime from ~20s to <1s.

Pipeline:
  1. Load & enhance (contrast, sharpen)
  2. Smart crop to content
  3. Aspect-ratio-preserving resize (4× target)
  4. Fast quantise to intermediate palette (Pillow C)
  5. Map intermediate palette → bead palette (Lab KD-tree, ≤256 lookups)
  6. Top-N colour selection + remap fallback
  7. Apply bead palette to image
  8. Downsample to grid
  9. Render grid + legend
  10. Composite & export PNG
"""

from __future__ import annotations

import math
from collections import Counter
from io import BytesIO
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from .colormap import get_mapper


# ═══════════════════════════════════════════════════════════════════════
# Design tokens
# ═══════════════════════════════════════════════════════════════════════

BG_COLOR       = (248, 248, 250)
GRID_BG        = (255, 255, 255)
COORD_TEXT     = (140, 140, 150)
LEGEND_BG      = (255, 255, 255)
LEGEND_BORDER  = (220, 220, 228)
TEXT_PRIMARY   = (30, 30, 37)
TEXT_SECONDARY = (130, 130, 142)
BEAD_SHADOW    = (185, 185, 195)
SEPARATOR      = (225, 225, 232)


# ═══════════════════════════════════════════════════════════════════════
# Font
# ═══════════════════════════════════════════════════════════════════════

def _font(size: int, bold: bool = False):
    from PIL import ImageFont
    paths = [
        "C:\\Windows\\Fonts\\msyh.ttc",
        "C:\\Windows\\Fonts\\msyhbd.ttc",
        "C:\\Windows\\Fonts\\simhei.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for fp in paths:
        try: return ImageFont.truetype(fp, size)
        except (OSError, IOError): continue
    return ImageFont.load_default()


# ═══════════════════════════════════════════════════════════════════════
# Preprocessing
# ═══════════════════════════════════════════════════════════════════════

def _load(data: bytes) -> Image.Image:
    img = Image.open(BytesIO(data))
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        return bg
    return img.convert("RGB") if img.mode != "RGB" else img


def _enhance(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Contrast(img).enhance(1.12)
    img = ImageEnhance.Color(img).enhance(1.05)
    return img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=50, threshold=3))


def _crop(img: Image.Image, margin: float = 0.03) -> Image.Image:
    gray = img.convert("L")
    w, h = gray.size
    threshold = 248
    left, top, right, bottom = w, h, 0, 0
    px = gray.load()
    for y in range(h):
        for x in range(w):
            if px[x, y] < threshold:  # type: ignore[index]
                if x < left:   left = x
                if x > right:  right = x
                if y < top:    top = y
                if y > bottom: bottom = y
    if left >= right or top >= bottom:
        return img
    mw, mh = int((right - left) * margin), int((bottom - top) * margin)
    return img.crop((
        max(0, left - mw), max(0, top - mh),
        min(w, right + mw), min(h, bottom + mh),
    ))


def _resize_keep_aspect(img: Image.Image, grid: int) -> Image.Image:
    """Resize to 4× grid, preserving aspect ratio with letterbox."""
    pre = grid * 4
    w, h = img.size
    ratio = pre / max(w, h)
    nw, nh = max(1, int(w * ratio)), max(1, int(h * ratio))
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (pre, pre), (255, 255, 255))
    canvas.paste(img, ((pre - nw) // 2, (pre - nh) // 2))
    return canvas


# ═══════════════════════════════════════════════════════════════════════
# Colour mapping (optimised — palette-level, not pixel-level)
# ═══════════════════════════════════════════════════════════════════════

def _fast_quantize(img: Image.Image, max_colors: int = 256) -> Image.Image:
    """Pillow C-level quantize — instant even for large images."""
    return img.quantize(colors=min(max_colors, 256), method=Image.Quantize.MEDIANCUT)


def _map_to_beads(
    img: Image.Image,
    brand: str,
    n_colors: int,
) -> Tuple[Image.Image, dict]:
    """
    Map image colours to professional bead palette.

    Strategy: work at the PALETTE level (≤256 entries), not pixel level.
    This is 100× faster than per-pixel Lab KD-tree mapping.
    """
    mapper = get_mapper(brand)

    # 1. Quantise to intermediate palette (C speed)
    quantized = _fast_quantize(img)
    palette_img = quantized.convert("RGB")

    # 2. Get the intermediate palette and pixel counts
    # getcolors() on a P-mode image returns [(count, palette_index), ...]
    raw_counts = quantized.getcolors()
    if not raw_counts:
        counter: Counter = Counter()
        for p in palette_img.getdata():  # type: ignore[arg-type]
            counter[p] += 1
        raw_counts = [(v, k) for k, v in counter.items()]

    # Convert palette indices → RGB tuples
    if quantized.mode == "P":
        palette = quantized.getpalette()
        color_counts = [
            (count, (palette[idx*3], palette[idx*3+1], palette[idx*3+2]))
            for count, idx in raw_counts
        ]
    else:
        color_counts = raw_counts

    # Sort by frequency
    color_counts.sort(key=lambda x: x[0], reverse=True)

    # 3. Map each palette entry to nearest bead colour (≤256 lookups!)
    bead_lut: dict[Tuple[int, int, int], Tuple[str, str, Tuple[int, int, int]]] = {}
    usage: dict[str, int] = {}
    for count, src_color in color_counts:
        code, name, brgb = mapper.map(src_color[0], src_color[1], src_color[2])
        bead_lut[src_color] = (code, name, brgb)
        usage[code] = usage.get(code, 0) + count

    # 4. Select top-N bead colours
    top_codes = sorted(usage, key=usage.get, reverse=True)[:n_colors]  # type: ignore[arg-type]
    top_set = set(top_codes)

    # 5. Build fast fallback mapper for colours outside top-N
    from .colormap import _rgb_to_lab
    top_rgbs: list = []
    top_info: list = []
    seen = set()
    for _, src_color in color_counts:
        code, name, brgb = bead_lut[src_color]
        if code in top_set and brgb not in seen:
            seen.add(brgb)
            top_rgbs.append(brgb)
            top_info.append((code, name, brgb))
    top_labs = [_rgb_to_lab(*rgb) for rgb in top_rgbs]

    def nearest_in_top(r: int, g: int, b: int):
        t = _rgb_to_lab(r, g, b)
        best_i, best_d = 0, float("inf")
        for i, lab in enumerate(top_labs):
            d = (t[0]-lab[0])**2 + (t[1]-lab[1])**2 + (t[2]-lab[2])**2
            if d < best_d:
                best_d, best_i = d, i
        return top_info[best_i]

    # 6. Build final palette-to-bead LUT
    final_lut: dict = {}
    for _, src_color in color_counts:
        code, name, brgb = bead_lut[src_color]
        if code not in top_set:
            code, name, brgb = nearest_in_top(src_color[0], src_color[1], src_color[2])
        final_lut[src_color] = brgb

    # 7. Apply the LUT to produce the output image
    pixels = list(palette_img.getdata())  # type: ignore[arg-type]
    out_pixels = [final_lut[p] for p in pixels]  # type: ignore[index]
    out = Image.new("RGB", img.size)
    out.putdata(out_pixels)  # type: ignore[arg-type]

    # 8. Build stats
    final_counts: dict[Tuple[int, int, int], int] = {}
    for p in out_pixels:
        final_counts[p] = final_counts.get(p, 0) + 1  # type: ignore[index]

    sorted_rgbs = sorted(final_counts, key=final_counts.get, reverse=True)  # type: ignore[arg-type]
    remap_codes, remap_names = [], []
    for rgb in sorted_rgbs:
        code, name, _ = mapper.map(rgb[0], rgb[1], rgb[2])
        remap_codes.append(code)
        remap_names.append(name)

    stats = {
        "codes":  remap_codes,
        "names":  remap_names,
        "rgb":    [list(rgb) for rgb in sorted_rgbs],
        "counts": [final_counts[rgb] for rgb in sorted_rgbs],
        "total":  sum(final_counts.values()),
        "brand":  brand,
    }
    return out, stats


# ═══════════════════════════════════════════════════════════════════════
# Rendering
# ═══════════════════════════════════════════════════════════════════════

def _draw_bead(draw: ImageDraw.Draw, x: int, y: int, s: int, color: tuple):
    pad = max(1, s // 10)
    r = max(2, s // 4)
    draw.rounded_rectangle([x+pad, y+pad, x+s, y+s], radius=r, fill=BEAD_SHADOW)
    draw.rounded_rectangle([x, y, x+s-pad, y+s-pad], radius=r, fill=color)
    hl = max(1, s // 5)
    draw.rounded_rectangle([x+pad, y+pad, x+pad+hl, y+pad+hl], radius=hl//2, fill=(255,255,255,35))


def _render_grid(img: Image.Image, grid_size: int, cell_size: int = 28) -> Image.Image:
    font = _font(max(8, cell_size // 3))
    margin = cell_size
    ow = grid_size * cell_size + margin
    oh = grid_size * cell_size + margin
    canvas = Image.new("RGBA", (ow, oh), GRID_BG)
    draw = ImageDraw.Draw(canvas)
    px = img.load()
    for r in range(grid_size):
        for c in range(grid_size):
            color = px[c, r]  # type: ignore[index]
            _draw_bead(draw, margin + c * cell_size, margin + r * cell_size, cell_size, color)
    # column numbers
    for c in range(grid_size):
        txt = str(c + 1)
        x = margin + c * cell_size + cell_size // 2
        bbox = draw.textbbox((0, 0), txt, font=font)
        draw.text((x - (bbox[2]-bbox[0])//2, 4), txt, fill=COORD_TEXT, font=font)
    # row numbers
    for r in range(grid_size):
        txt = str(r + 1)
        y = margin + r * cell_size + cell_size // 2
        bbox = draw.textbbox((0, 0), txt, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.text((margin - tw - 5, y - th//2), txt, fill=COORD_TEXT, font=font)
    return canvas


def _render_legend(stats: dict, grid_size: int, cell_size: int) -> Image.Image:
    codes, names, rgbs, counts = stats["codes"], stats["names"], stats["rgb"], stats["counts"]
    total, brand = stats["total"], stats["brand"].upper()

    font_title = _font(16, bold=True)
    font_item  = _font(12)
    font_small = _font(11)

    swatch, gap = 18, 10
    cols = min(len(codes), 5)
    rows = math.ceil(len(codes) / cols)
    col_w = swatch + 6 + 62 + 44 + gap

    pad = 22
    header_h, total_h = 56, 34
    items_h = rows * (swatch + gap) - gap

    cw = pad*2 + cols*col_w - gap
    ch = pad*2 + header_h + items_h + total_h

    leg = Image.new("RGBA", (cw, ch), (248,248,250,0))
    draw = ImageDraw.Draw(leg)
    draw.rounded_rectangle([0,0,cw,ch], radius=16, fill=LEGEND_BG, outline=LEGEND_BORDER, width=1)

    # header
    draw.text((pad, pad), f"颜色图例  ·  {brand}", fill=TEXT_PRIMARY, font=font_title)
    draw.line([(pad, pad+38), (cw-pad, pad+38)], fill=SEPARATOR, width=1)

    # items
    base_y = pad + header_h
    for idx in range(len(codes)):
        r, c = idx // cols, idx % cols
        x, y = pad + c*col_w, base_y + r*(swatch+gap)
        rgb = tuple(rgbs[idx])
        draw.rounded_rectangle([x,y,x+swatch,y+swatch], radius=4, fill=rgb, outline=(200,200,208), width=1)
        draw.text((x+swatch+6, y-1), codes[idx], fill=TEXT_PRIMARY, font=font_item)
        draw.text((x+swatch+6, y+swatch-11), names[idx], fill=TEXT_SECONDARY, font=font_small)
        pct = counts[idx]/total*100 if total else 0
        draw.text((x+swatch+70, y), f"{pct:.1f}%", fill=TEXT_SECONDARY, font=font_item)
        draw.text((x+swatch+70, y+swatch-11), f"×{counts[idx]}", fill=TEXT_SECONDARY, font=font_small)

    # total
    sep_y = base_y + items_h + 8
    draw.line([(pad, sep_y), (cw-pad, sep_y)], fill=SEPARATOR, width=1)
    info = f"共 {total:,} 颗  ·  {grid_size}×{grid_size}  ·  {len(codes)} 色"
    bbox = draw.textbbox((0,0), info, font=font_item)
    tw = bbox[2]-bbox[0]
    draw.text(((cw-tw)//2, sep_y+10), info, fill=TEXT_SECONDARY, font=font_item)
    return leg


# ═══════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════

def process(
    data: bytes,
    grid_size: int = 48,
    n_colors: int = 48,
    brand: str = "artkal",
    cell_size: int = 28,
) -> Tuple[bytes, dict]:
    """
    Produce a professional bead-art blueprint.

    Parameters
    ----------
    data      : bytes   Raw image bytes.
    grid_size : int     Beads per side (16/29/32/48/58/64).
    n_colors  : int     Max bead colours (16/24/32/48/64/80/96/128/256).
    brand     : str     "artkal" or "perler".
    cell_size : int     Pixels per bead cell.

    Returns
    -------
    (png_bytes, stats_dict)
    """
    n_colors = min(n_colors, grid_size * grid_size)

    # 1-3. Load → enhance → crop → resize
    img = _load(data)
    img = _enhance(img)
    img = _crop(img)
    img = _resize_keep_aspect(img, grid_size)

    # 4-5. Fast quantize → map palette to bead colours
    img, stats = _map_to_beads(img, brand, n_colors)

    # 6. Downsample to grid
    img = img.resize((grid_size, grid_size), Image.NEAREST)

    # Recount after downsample for accurate stats
    from collections import Counter as _Counter
    cnt: _Counter = _Counter()
    for p in img.getdata():  # type: ignore[arg-type]
        cnt[p] += 1
    sorted_items = cnt.most_common()
    mapper = get_mapper(brand)
    stats["rgb"]    = [list(it[0]) for it in sorted_items]
    stats["counts"]  = [it[1] for it in sorted_items]
    stats["total"]   = sum(it[1] for it in sorted_items)
    stats["codes"]   = []
    stats["names"]   = []
    for rgb in stats["rgb"]:
        c, n, _ = mapper.map(rgb[0], rgb[1], rgb[2])
        stats["codes"].append(c)
        stats["names"].append(n)
    stats["brand"] = brand

    # 7-8. Render
    grid_img = _render_grid(img, grid_size, cell_size)
    legend   = _render_legend(stats, grid_size, cell_size)

    # 9. Composite
    spacer = 28
    fw = max(grid_img.width, legend.width)
    fh = grid_img.height + spacer + legend.height
    canvas = Image.new("RGBA", (fw, fh), BG_COLOR)
    canvas.paste(grid_img, ((fw - grid_img.width)//2, 0))
    canvas.paste(legend, ((fw - legend.width)//2, grid_img.height + spacer), legend)

    buf = BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue(), stats
