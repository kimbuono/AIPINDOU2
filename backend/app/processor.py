"""
V3 Image processor — professional bead-art blueprint generation.

Pipeline:
  1. Load & auto-enhance (contrast, sharpen, denoise)
  2. Smart crop to content
  3. Aspect-ratio-preserving resize with letterbox
  4. Colour quantisation via professional bead palettes (Lab KD-tree)
  5. Render bead grid with row/column coordinates
  6. Render professional legend (code, name, count, percentage)
  7. Composite & export high-resolution PNG
"""

from __future__ import annotations

import math
from io import BytesIO
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from .colormap import get_mapper


# ═══════════════════════════════════════════════════════════════════════
# Design tokens
# ═══════════════════════════════════════════════════════════════════════

BG_COLOR       = (248, 248, 250)
GRID_BG        = (255, 255, 255)
GRID_LINE      = (190, 190, 198)
COORD_TEXT     = (140, 140, 150)
LEGEND_BG      = (255, 255, 255)
LEGEND_BORDER  = (220, 220, 228)
TEXT_PRIMARY   = (30, 30, 37)
TEXT_SECONDARY = (130, 130, 142)
BEAD_SHADOW    = (185, 185, 195)
SEPARATOR      = (225, 225, 232)


# ═══════════════════════════════════════════════════════════════════════
# Font helpers
# ═══════════════════════════════════════════════════════════════════════

def _load_font(size: int, bold: bool = False):
    paths = [
        "C:\\Windows\\Fonts\\msyh.ttc",
        "C:\\Windows\\Fonts\\msyhbd.ttc",
        "C:\\Windows\\Fonts\\simhei.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for fp in paths:
        try:
            from PIL import ImageFont
            return ImageFont.truetype(fp, size)
        except (OSError, IOError):
            continue
    from PIL import ImageFont
    return ImageFont.load_default()


# ═══════════════════════════════════════════════════════════════════════
# Image preprocessing
# ═══════════════════════════════════════════════════════════════════════

def _load(data: bytes) -> Image.Image:
    img = Image.open(BytesIO(data))
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    return img


def _auto_enhance(img: Image.Image) -> Image.Image:
    """Improve contrast, apply mild sharpen, slight denoise."""
    # 1. mild contrast stretch
    enh = ImageEnhance.Contrast(img)
    img = enh.enhance(1.15)
    # 2. slight colour saturation boost
    enh = ImageEnhance.Color(img)
    img = enh.enhance(1.08)
    # 3. subtle sharpen
    img = img.filter(ImageFilter.UnsharpMask(radius=0.6, percent=60, threshold=4))
    return img


def _crop_to_content(img: Image.Image, margin_pct: float = 0.04) -> Image.Image:
    """
    Auto-crop whitespace / near-white borders.
    Leaves *margin_pct* padding around the detected content.
    """
    gray = img.convert("L")
    # threshold: anything darker than 245 is "content"
    threshold = 245
    w, h = gray.size

    # find bounding box of non-background pixels
    left, top, right, bottom = w, h, 0, 0
    pixels = gray.load()
    for y in range(h):
        for x in range(w):
            if pixels[x, y] < threshold:  # type: ignore[index]
                if x < left:   left = x
                if x > right:  right = x
                if y < top:    top = y
                if y > bottom: bottom = y

    # if nothing detected, return original
    if left >= right or top >= bottom:
        return img

    # add margin
    mw = int((right - left) * margin_pct)
    mh = int((bottom - top) * margin_pct)
    left   = max(0, left - mw)
    top    = max(0, top - mh)
    right  = min(w, right + mw)
    bottom = min(h, bottom + mh)

    return img.crop((left, top, right, bottom))


def _resize_keep_aspect(
    img: Image.Image,
    grid_size: int,
    bg: Tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """
    Resize so the longer side fits exactly into *grid_size*.
    The shorter side is centred on a white background (letterbox).
    """
    pre = grid_size * 4  # work at 4× for detail preservation
    w, h = img.size
    ratio = pre / max(w, h)
    new_w = max(1, int(w * ratio))
    new_h = max(1, int(h * ratio))
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # centre on square canvas
    canvas = Image.new("RGB", (pre, pre), bg)
    ox = (pre - new_w) // 2
    oy = (pre - new_h) // 2
    canvas.paste(img, (ox, oy))
    return canvas


# ═══════════════════════════════════════════════════════════════════════
# Colour mapping
# ═══════════════════════════════════════════════════════════════════════

def _map_to_palette(
    img: Image.Image,
    brand: str,
    n_colors: int,
) -> Tuple[Image.Image, dict]:
    """
    Map every pixel to nearest bead colour. Returns (mapped_img, stats).

    stats: { "codes": [...], "names": [...], "rgb": [...], "counts": [...], "total": int }
    """
    mapper = get_mapper(brand)
    w, h = img.size
    pixels = list(img.getdata())  # type: ignore[arg-type]

    # Build colour reduction: find the top *n_colors* most-used bead colours
    # across the image, then snap every pixel
    # Step 1: map all unique pixels to bead colours
    unique_src = set(pixels)
    bead_map: dict[Tuple[int, int, int], Tuple[str, str, Tuple[int, int, int]]] = {}
    usage: dict[str, int] = {}
    for p in unique_src:
        code, name, brgb = mapper.map(p[0], p[1], p[2])  # type: ignore[index]
        bead_map[p] = (code, name, brgb)  # type: ignore[index]
        usage[code] = usage.get(code, 0) + 1

    # Step 2: keep only the top n_colors bead colours by usage
    top_codes = sorted(usage, key=usage.get, reverse=True)[:n_colors]  # type: ignore[arg-type]
    top_set = set(top_codes)

    # Step 3: for pixels whose bead colour isn't in top N, remap to nearest in top N
    # Build a small mapper just for the allowed bead colours
    allowed_rgbs = [bead_map[p][2] for p in unique_src if bead_map[p][0] in top_set]
    allowed_codes_names = [(bead_map[p][0], bead_map[p][1]) for p in unique_src if bead_map[p][0] in top_set]
    # deduplicate
    seen = set()
    dedup_rgb = []
    dedup_cn = []
    for rgb, cn in zip(allowed_rgbs, allowed_codes_names):
        if rgb not in seen:
            seen.add(rgb)
            dedup_rgb.append(rgb)
            dedup_cn.append(cn)

    # Build a fast lookup for the fallback mapping
    from .colormap import _rgb_to_lab
    top_lab = [_rgb_to_lab(*rgb) for rgb in dedup_rgb]

    def _nearest_top(r: int, g: int, b: int):
        target = _rgb_to_lab(r, g, b)
        best_i, best_d = 0, float("inf")
        for i, lab in enumerate(top_lab):
            d = sum((a - b) ** 2 for a, b in zip(target, lab))
            if d < best_d:
                best_d = d
                best_i = i
        return dedup_cn[best_i][0], dedup_cn[best_i][1], dedup_rgb[best_i]

    # Step 4: final mapping pass
    final_codes: dict[Tuple[int, int, int], Tuple[str, str, Tuple[int, int, int]]] = {}
    for p in unique_src:
        code, name, brgb = bead_map[p]  # type: ignore[index]
        if code not in top_set:
            code, name, brgb = _nearest_top(p[0], p[1], p[2])  # type: ignore[index]
        final_codes[p] = (code, name, brgb)  # type: ignore[index]

    # Build the output image & count per code
    out_pixels = [final_codes[p][2] for p in pixels]  # type: ignore[index]
    out = Image.new("RGB", (w, h))
    out.putdata(out_pixels)  # type: ignore[arg-type]

    # Counts
    code_counts: dict[str, int] = {}
    code_names: dict[str, str] = {}
    code_rgb: dict[str, Tuple[int, int, int]] = {}
    for p in unique_src:
        c, n, r = final_codes[p]  # type: ignore[index]
        code_counts[c] = code_counts.get(c, 0) + (list(pixels).count(p))  # This is slow, let's fix
        code_names[c] = n
        code_rgb[c] = r

    # Better counting: iterate over final output
    code_counts = {}
    for _, name, rgb in final_codes.values():  # type: ignore[misc]
        pass  # We need to recount properly

    # Actually recount properly
    code_counts = {}
    for p, src_p in zip(out_pixels, pixels):
        # Find which code this maps to
        c = final_codes[src_p][0]  # type: ignore[index]
        code_counts[c] = code_counts.get(c, 0) + 1
        code_names[c] = final_codes[src_p][1]  # type: ignore[index]
        code_rgb[c] = final_codes[src_p][2]  # type: ignore[index]

    # Sort by count desc
    sorted_codes = sorted(code_counts, key=code_counts.get, reverse=True)  # type: ignore[arg-type]

    stats = {
        "codes":  sorted_codes,
        "names":  [code_names[c] for c in sorted_codes],
        "rgb":    [code_rgb[c] for c in sorted_codes],
        "counts": [code_counts[c] for c in sorted_codes],
        "total":  sum(code_counts.values()),
        "brand":  brand,
    }
    return out, stats


# ═══════════════════════════════════════════════════════════════════════
# Rendering
# ═══════════════════════════════════════════════════════════════════════

def _draw_bead(
    draw: ImageDraw.Draw,
    x: int, y: int,
    size: int,
    color: Tuple[int, int, int],
) -> None:
    """Single bead cell: rounded rect + shadow + highlight."""
    pad = max(1, size // 10)
    r = max(2, size // 4)
    # shadow
    draw.rounded_rectangle(
        [x + pad, y + pad, x + size, y + size],
        radius=r, fill=BEAD_SHADOW,
    )
    # body
    draw.rounded_rectangle(
        [x, y, x + size - pad, y + size - pad],
        radius=r, fill=color,
    )
    # highlight
    hl = max(1, size // 5)
    draw.rounded_rectangle(
        [x + pad, y + pad, x + pad + hl, y + pad + hl],
        radius=hl // 2, fill=(255, 255, 255, 35),
    )


def _render_grid(
    img: Image.Image,
    grid_size: int,
    cell_size: int = 28,
) -> Image.Image:
    """Render bead grid with coordinate labels."""
    font = _load_font(max(8, cell_size // 3))
    margin = cell_size  # space for coordinates
    out_w = grid_size * cell_size + margin
    out_h = grid_size * cell_size + margin

    canvas = Image.new("RGBA", (out_w, out_h), GRID_BG)
    draw = ImageDraw.Draw(canvas)

    pixels = img.load()
    for r in range(grid_size):
        for c in range(grid_size):
            color = pixels[c, r]  # type: ignore[index]
            x = margin + c * cell_size
            y = margin + r * cell_size
            _draw_bead(draw, x, y, cell_size, color)

    # column numbers (top)
    for c in range(grid_size):
        x = margin + c * cell_size + cell_size // 2
        txt = str(c + 1)
        bbox = draw.textbbox((0, 0), txt, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw // 2, 3), txt, fill=COORD_TEXT, font=font)

    # row numbers (left)
    for r in range(grid_size):
        y = margin + r * cell_size + cell_size // 2
        txt = str(r + 1)
        bbox = draw.textbbox((0, 0), txt, font=font)
        th = bbox[3] - bbox[1]
        tw = bbox[2] - bbox[0]
        draw.text((margin - tw - 5, y - th // 2), txt, fill=COORD_TEXT, font=font)

    return canvas


def _render_legend(
    stats: dict,
    grid_size: int,
    cell_size: int,
) -> Image.Image:
    """Professional legend card with brand info, codes, names, counts."""
    codes  = stats["codes"]
    names  = stats["names"]
    rgbs   = stats["rgb"]
    counts = stats["counts"]
    total  = stats["total"]
    brand  = stats["brand"].upper()

    font_title = _load_font(16, bold=True)
    font_item  = _load_font(12)
    font_small = _load_font(11)

    swatch = 18
    gap = 10
    cols = min(len(codes), 5)
    rows = math.ceil(len(codes) / cols)

    # card dimensions
    card_pad = 22
    title_h = 32
    header_h = 56
    total_h = 34

    col_w = swatch + 6 + 62 + 44 + gap
    content_w = cols * col_w - gap
    card_w = card_pad * 2 + content_w
    items_h = rows * (swatch + gap) - gap
    card_h = card_pad * 2 + header_h + items_h + total_h

    legend = Image.new("RGBA", (card_w, card_h), (248, 248, 250, 0))
    draw = ImageDraw.Draw(legend)

    # card bg
    draw.rounded_rectangle([0, 0, card_w, card_h], radius=16, fill=LEGEND_BG, outline=LEGEND_BORDER, width=1)

    # header
    draw.text((card_pad, card_pad), f"颜色图例  ·  {brand}", fill=TEXT_PRIMARY, font=font_title)
    draw.line([(card_pad, card_pad + title_h + 6), (card_w - card_pad, card_pad + title_h + 6)], fill=SEPARATOR, width=1)

    # items
    base_y = card_pad + header_h
    for idx in range(len(codes)):
        r = idx // cols
        c = idx % cols
        x = card_pad + c * col_w
        y = base_y + r * (swatch + gap)

        rgb = rgbs[idx]
        draw.rounded_rectangle([x, y, x + swatch, y + swatch], radius=4, fill=rgb, outline=(200, 200, 208), width=1)
        draw.text((x + swatch + 6, y - 1), codes[idx], fill=TEXT_PRIMARY, font=font_item)
        draw.text((x + swatch + 6, y + swatch - 11), names[idx], fill=TEXT_SECONDARY, font=font_small)
        count_str = f"×{counts[idx]}"
        pct = counts[idx] / total * 100 if total else 0
        draw.text((x + swatch + 70, y), f"{pct:.1f}%", fill=TEXT_SECONDARY, font=font_item)
        draw.text((x + swatch + 70, y + swatch - 11), count_str, fill=TEXT_SECONDARY, font=font_small)

    # total row
    sep_y = base_y + items_h + 8
    draw.line([(card_pad, sep_y), (card_w - card_pad, sep_y)], fill=SEPARATOR, width=1)
    info = f"共 {total:,} 颗  ·  {grid_size}×{grid_size}  ·  {len(codes)} 色"
    bbox = draw.textbbox((0, 0), info, font=font_item)
    tw = bbox[2] - bbox[0]
    draw.text(((card_w - tw) // 2, sep_y + 10), info, fill=TEXT_SECONDARY, font=font_item)

    return legend


# ═══════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════

def process(
    data: bytes,
    grid_size: int = 48,
    n_colors: int = 32,
    brand: str = "artkal",
    cell_size: int = 28,
) -> Tuple[bytes, dict]:
    """
    Produce a professional bead-art blueprint.

    Parameters
    ----------
    data      : bytes   Raw JPEG / PNG / WebP bytes.
    grid_size : int     Beads per side.
    n_colors  : int     Max distinct bead colours.
    brand     : str     "artkal" or "perler".
    cell_size : int     Pixels per bead cell in output.

    Returns
    -------
    (png_bytes, stats_dict)
    """
    n_colors = min(n_colors, grid_size * grid_size)

    # 1. load + enhance
    img = _load(data)
    img = _auto_enhance(img)

    # 2. smart crop
    img = _crop_to_content(img)

    # 3. aspect-ratio-preserving resize
    img = _resize_keep_aspect(img, grid_size)

    # 4. map to professional bead palette
    img, stats = _map_to_palette(img, brand, n_colors)

    # 5. downsample to grid
    img = img.resize((grid_size, grid_size), Image.NEAREST)

    # 6. recount after downsample (because NEAREST may change distribution)
    # Re-extract stats from the final grid image
    from collections import Counter
    final_pixels = list(img.getdata())  # type: ignore[arg-type]
    # Map these to codes via the original mapping (reuse bead_map concept)
    # For simplicity, just recount the visual colors in the final grid
    pixel_counts: Counter = Counter()
    for p in final_pixels:
        pixel_counts[p] += 1

    # Sort by count desc and rebuild stats
    sorted_items = pixel_counts.most_common()
    stats["rgb"] = [item[0] for item in sorted_items]
    stats["counts"] = [item[1] for item in sorted_items]
    stats["total"] = sum(item[1] for item in sorted_items)

    # We lost codes/names in the final grid - remap using the mapper
    mapper = get_mapper(brand)
    final_codes = []
    final_names = []
    for rgb in stats["rgb"]:
        code, name, _ = mapper.map(rgb[0], rgb[1], rgb[2])
        final_codes.append(code)
        final_names.append(name)
    stats["codes"] = final_codes
    stats["names"] = final_names

    # 7. render grid + legend
    grid_img = _render_grid(img, grid_size, cell_size)
    legend   = _render_legend(stats, grid_size, cell_size)

    # 8. composite
    spacer = 28
    final_w = max(grid_img.width, legend.width)
    final_h = grid_img.height + spacer + legend.height
    canvas = Image.new("RGBA", (final_w, final_h), BG_COLOR)
    canvas.paste(grid_img, (max(0, (final_w - grid_img.width) // 2), 0))
    lx = (final_w - legend.width) // 2
    canvas.paste(legend, (lx, grid_img.height + spacer), legend)

    buf = BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue(), stats
