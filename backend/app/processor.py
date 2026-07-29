"""
V3.1 Image processor — fast, professional bead-art blueprint generation.
"""

from __future__ import annotations

import logging
import math
import sys
import traceback
from collections import Counter as _Counter
from io import BytesIO
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from .colormap import get_mapper

logger = logging.getLogger("aipindou.processor")


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

def _map_to_beads(
    img: Image.Image,
    brand: str,
    n_colors: int,
    dither: bool = False,
) -> Tuple[Image.Image, dict]:
    """
    Map image to professional bead palette.

    Strategy: pixel-level CIEDE2000 mapping → select top-N unique bead
    colours actually used → Floyd-Steinberg dither within allowed palette.
    """
    from .color_engine import rgb_to_lab as _rgb_to_lab

    mapper = get_mapper(brand)
    pixels = list(img.getdata())  # type: ignore[arg-type]

    # 1. Map every pixel to nearest bead colour via CIEDE2000 KD-tree
    #    Build a cache for speed (unique colours only)
    unique_src = set(pixels)
    bead_map: dict = {}
    bead_usage: dict[str, int] = {}
    logger.info(f"  Mapping {len(unique_src)} unique colours to {brand} palette...")
    for p in unique_src:
        code, name, brgb = mapper.map(p[0], p[1], p[2])  # type: ignore[index]
        bead_map[p] = brgb  # type: ignore[index]
        bead_usage[code] = bead_usage.get(code, 0) + 1

    # 2. Select bead colours: use all colours present in the image, up
    #    to n_colors. If fewer are used, report honestly (physical limit
    #    of the bead palette for this image).
    sorted_codes = sorted(bead_usage, key=bead_usage.get, reverse=True)  # type: ignore[arg-type]
    # Use all unique bead colours that appear, capped at n_colors
    selected_codes = sorted_codes[:n_colors]
    # Build allowed RGB palette
    top_rgbs = list({bead_map[p] for p in unique_src
                     if mapper.map(p[0], p[1], p[2])[0] in set(selected_codes)})  # type: ignore[index]
    # Sort by frequency for consistent dithering
    rgb_freq = {}
    for p in unique_src:
        bm = bead_map[p]  # type: ignore[index]
        rgb_freq[bm] = rgb_freq.get(bm, 0) + 1
    top_rgbs.sort(key=lambda x: rgb_freq.get(x, 0), reverse=True)
    logger.info(f"  Using {len(top_rgbs)} bead colours (max available for this image)")

    # 3. Apply pixel mapping: snap every pixel to nearest allowed bead
    #    colour (within the selected top-N), with dithering.
    # Build a fast remap LUT for pixels whose natural bead is outside top-N
    from .color_engine import rgb_to_lab as _rgb_to_lab
    top_labs = [_rgb_to_lab(*rgb) for rgb in top_rgbs]

    def _snap_to_top(r, g, b):
        t = _rgb_to_lab(r, g, b)
        bi, bd = 0, float("inf")
        for i, lab in enumerate(top_labs):
            d = (t[0]-lab[0])**2 + (t[1]-lab[1])**2 + (t[2]-lab[2])**2
            if d < bd:
                bd, bi = d, i
        return top_rgbs[bi]

    remap_lut = {}
    for p in unique_src:
        bm = bead_map[p]  # type: ignore[index]
        if bm in top_rgbs:
            remap_lut[p] = bm  # type: ignore[index]
        else:
            remap_lut[p] = _snap_to_top(p[0], p[1], p[2])  # type: ignore[index]

    if dither and len(top_rgbs) >= 2:
        from .color_engine import floyd_steinberg_dither
        out_pixels = floyd_steinberg_dither(
            [(p[0], p[1], p[2]) for p in pixels],  # type: ignore[index]
            img.size[0], img.size[1],
            top_rgbs,
        )
    else:
        out_pixels = [remap_lut[p] for p in pixels]  # type: ignore[index]

    out = Image.new("RGB", img.size)
    out.putdata(out_pixels)  # type: ignore[arg-type]

    # 4. Count stats
    pixel_counter = _Counter()
    for px in out_pixels:
        pixel_counter[px] += 1
    sorted_rgbs = [rgb for rgb, _ in pixel_counter.most_common()]

    codes, names = [], []
    for rgb in sorted_rgbs:
        c, n, _ = mapper.map(rgb[0], rgb[1], rgb[2])
        codes.append(c)
        names.append(n)

    stats = {
        "codes":  codes,
        "names":  names,
        "rgb":    [list(rgb) for rgb in sorted_rgbs],
        "counts": [pixel_counter[rgb] for rgb in sorted_rgbs],
        "total":  sum(pixel_counter.values()),
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

def recommend_size(w: int, h: int, complexity: float = 0.5) -> int:
    """
    Auto-recommend grid size based on image dimensions and complexity.
    Returns a valid grid size from the supported set.
    """
    pixels = w * h
    # Base size from total pixels
    base = int(math.sqrt(pixels) / 8)
    # Adjust for complexity (more complex → larger grid)
    adjusted = int(base * (0.6 + complexity * 0.8))
    # Snap to nearest valid size
    valid = [16, 29, 32, 48, 58, 64]
    return min(valid, key=lambda v: abs(v - adjusted))


def process(
    data: bytes,
    grid_size: int = 48,
    n_colors: int = 48,
    brand: str = "artkal",
    cell_size: int = 28,
    dither: bool = True,
) -> Tuple[bytes, dict]:
    n_colors = min(n_colors, grid_size * grid_size)

    try:
        logger.info(f"[1/9] 加载图片: {len(data):,} bytes")
        img = _load(data)
        logger.info(f"[1/9] 加载成功: {img.size}, mode={img.mode}")
    except Exception:
        logger.error(f"[1/9] 加载失败:\n{traceback.format_exc()}")
        raise

    try:
        logger.info(f"[2/9] 图像增强中...")
        img = _enhance(img)
        logger.info(f"[2/9] 增强完成: {img.size}")
    except Exception:
        logger.error(f"[2/9] 增强失败:\n{traceback.format_exc()}")
        raise

    try:
        logger.info(f"[3/9] 裁剪空白区域...")
        img = _crop(img)
        logger.info(f"[3/9] 裁剪完成: {img.size}")
    except Exception:
        logger.error(f"[3/9] 裁剪失败:\n{traceback.format_exc()}")
        raise

    try:
        logger.info(f"[4/9] 等比缩放至 {grid_size}...")
        img = _resize_keep_aspect(img, grid_size)
        logger.info(f"[4/9] 缩放完成: {img.size}")
    except Exception:
        logger.error(f"[4/9] 缩放失败:\n{traceback.format_exc()}")
        raise

    try:
        logger.info(f"[5/9] CIEDE2000 色彩映射 brand={brand} colors={n_colors} dither={dither}...")
        img, stats = _map_to_beads(img, brand, n_colors, dither=dither)
        logger.info(f"[5/9] 映射完成: {len(stats.get('codes',[]))} 色")
    except Exception:
        logger.error(f"[5/9] 颜色映射失败:\n{traceback.format_exc()}")
        raise

    try:
        logger.info(f"[6/9] 降采样至目标网格...")
        img = img.resize((grid_size, grid_size), Image.NEAREST)
        logger.info(f"[6/9] 降采样完成: {img.size}")
    except Exception:
        logger.error(f"[6/9] 降采样失败:\n{traceback.format_exc()}")
        raise

    try:
        logger.info(f"[7/9] 统计颜色数据...")
        from collections import Counter as _Counter
        cnt: _Counter = _Counter()
        for p in img.getdata():
            cnt[p] += 1
        sorted_items = cnt.most_common()
        mapper = get_mapper(brand)
        stats["rgb"]    = [list(it[0]) for it in sorted_items]
        stats["counts"]  = [it[1] for it in sorted_items]
        stats["total"]   = sum(it[1] for it in sorted_items)
        stats["codes"]   = []
        stats["names"]   = []
        for rgb_item in stats["rgb"]:
            c, n, _ = mapper.map(rgb_item[0], rgb_item[1], rgb_item[2])
            stats["codes"].append(c)
            stats["names"].append(n)
        stats["brand"] = brand
        stats["grid_size"] = grid_size
        stats["n_colors"] = len(stats["codes"])
        logger.info(f"[7/9] 统计完成: {stats['total']}颗, {stats['n_colors']}色")
    except Exception:
        logger.error(f"[7/9] 统计失败:\n{traceback.format_exc()}")
        raise

    try:
        logger.info(f"[8/9] 渲染图纸+图例...")
        grid_img = _render_grid(img, grid_size, cell_size)
        legend   = _render_legend(stats, grid_size, cell_size)
        logger.info(f"[8/9] 渲染完成: grid={grid_img.size}, legend={legend.size}")
    except Exception:
        logger.error(f"[8/9] 渲染失败:\n{traceback.format_exc()}")
        raise

    try:
        logger.info(f"[9/9] 合成+编码PNG...")
        spacer = 28
        fw = max(grid_img.width, legend.width)
        fh = grid_img.height + spacer + legend.height
        canvas = Image.new("RGBA", (fw, fh), BG_COLOR)
        canvas.paste(grid_img, ((fw - grid_img.width)//2, 0))
        canvas.paste(legend, ((fw - legend.width)//2, grid_img.height + spacer), legend)
        buf = BytesIO()
        canvas.save(buf, format="PNG")
        result = buf.getvalue()
        logger.info(f"[9/9] 完成: PNG {len(result):,} bytes, {fw}x{fh}")
        return result, stats
    except Exception:
        logger.error(f"[9/9] 合成失败:\n{traceback.format_exc()}")
        raise
