"""
Image processor for bead art blueprint generation.

Pipeline:
  1. Load & normalize
  2. Pre-resize (LANCZOS, 4× target) to preserve detail
  3. K-means colour quantisation (pure Python, no heavy deps)
  4. Down-sample to target grid (NEAREST)
  5. Render bead cells with rounded corners & shadows
  6. Render colour legend with counts & total
  7. Composite & export PNG
"""

from __future__ import annotations

import math
import random
from io import BytesIO
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont


# ═══════════════════════════════════════════════════════════════════════
# K-means colour quantisation (pure Python)
# ═══════════════════════════════════════════════════════════════════════

def _kmeans_colors(
    pixels: List[Tuple[int, int, int]],
    k: int,
    max_iters: int = 20,
) -> List[Tuple[int, int, int]]:
    """
    Cluster *pixels* into *k* clusters, returning the k centroids.

    Uses k-means++ initialisation for better quality and stability.
    """
    if k >= len(pixels):
        return list(set(pixels))

    # --- k-means++ init ---
    centroids = [random.choice(pixels)]
    for _ in range(1, k):
        # compute squared distances to nearest centroid
        dists = [
            min(
                (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2
                for c in centroids
            )
            for p in pixels
        ]
        total = sum(dists)
        if total == 0:
            # all remaining points identical, break
            break
        r = random.random() * total
        cum = 0
        for i, d in enumerate(dists):
            cum += d
            if cum >= r:
                centroids.append(pixels[i])
                break

    # --- Lloyd iteration ---
    for _ in range(max_iters):
        # assign each pixel to nearest centroid
        assignments: List[List[Tuple[int, int, int]]] = [[] for _ in range(k)]
        for p in pixels:
            best_c = 0
            best_d = float("inf")
            for ci, c in enumerate(centroids):
                d = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2
                if d < best_d:
                    best_d = d
                    best_c = ci
            assignments[best_c].append(p)

        # recompute centroids
        new_centroids: List[Tuple[int, int, int]] = []
        for cluster in assignments:
            if not cluster:
                new_centroids.append(random.choice(pixels))
            else:
                n = len(cluster)
                new_centroids.append((
                    int(sum(p[0] for p in cluster) / n),
                    int(sum(p[1] for p in cluster) / n),
                    int(sum(p[2] for p in cluster) / n),
                ))

        if new_centroids == centroids:
            break
        centroids = new_centroids

    return centroids


# ═══════════════════════════════════════════════════════════════════════
# Font helpers
# ═══════════════════════════════════════════════════════════════════════

def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Load the best available TrueType font at *size*."""
    paths = [
        "C:\\Windows\\Fonts\\msyh.ttc",       # Microsoft YaHei (Chinese)
        "C:\\Windows\\Fonts\\simhei.ttf",      # SimHei (Chinese)
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for fp in paths:
        try:
            return ImageFont.truetype(fp, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _load_font_bold(size: int) -> ImageFont.FreeTypeFont:
    """Load a bold TrueType font at *size*."""
    paths = [
        "C:\\Windows\\Fonts\\msyhbd.ttc",
        "C:\\Windows\\Fonts\\simhei.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for fp in paths:
        try:
            return ImageFont.truetype(fp, size)
        except (OSError, IOError):
            continue
    return _load_font(size)


# ═══════════════════════════════════════════════════════════════════════
# Core pipeline
# ═══════════════════════════════════════════════════════════════════════

# colour palette for the background / UI chrome
BG = (248, 248, 250)
GRID_LINE = (210, 210, 215)
CARD_BG = (255, 255, 255)
TEXT_MAIN = (30, 30, 35)
TEXT_SECONDARY = (140, 140, 150)
BEAD_SHADOW = (190, 190, 198)
BEAD_HIGHLIGHT = (255, 255, 255, 40)


def _load_image(data: bytes) -> Image.Image:
    return Image.open(BytesIO(data)).convert("RGB")


def _resize_preserve(img: Image.Image, grid_size: int) -> Image.Image:
    """
    Pre-resize with LANCZOS to 4× the target grid.
    This preserves far more detail than a direct NEAREST down-sample.
    """
    pre = grid_size * 4
    w, h = img.size
    # crop to square centre
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    return img.resize((pre, pre), Image.LANCZOS)


def _quantize(img: Image.Image, n_colors: int) -> Image.Image:
    """K-means quantisation to *n_colors*."""
    w, h = img.size
    pixels = list(img.getdata())  # type: ignore[arg-type]

    # For large images, sample to speed up k-means
    sample_size = min(len(pixels), 4000)
    if len(pixels) > sample_size:
        sampled = random.sample(pixels, sample_size)
    else:
        sampled = pixels

    palette = _kmeans_colors(sampled, n_colors)

    # Build a lookup table: for every RGB triplet in the image, snap
    # to the nearest palette colour.
    # We build a dict for uniqueness across the image.
    lut: dict[Tuple[int, int, int], Tuple[int, int, int]] = {}
    for p in set(pixels):
        best = palette[0]
        best_d = float("inf")
        for c in palette:
            d = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2
            if d < best_d:
                best_d = d
                best = c
        lut[p] = best

    out = Image.new("RGB", (w, h))
    out.putdata([lut[p] for p in pixels])  # type: ignore[arg-type]
    return out


def _downsample(img: Image.Image, grid_size: int) -> Image.Image:
    """Downsample to final grid dimensions."""
    return img.resize((grid_size, grid_size), Image.NEAREST)


def _extract_palette(img: Image.Image) -> Tuple[List[Tuple[int, int, int]], List[int]]:
    """Return (colours, counts) sorted by frequency descending."""
    result = img.getcolors()
    if result is None:
        # fallback (should not happen for quantized images)
        counts_map: dict[Tuple[int, int, int], int] = {}
        for c in img.getdata():  # type: ignore[attr-defined]
            counts_map[c] = counts_map.get(c, 0) + 1  # type: ignore[index]
        result = [(v, k) for k, v in counts_map.items()]

    result.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in result], [item[0] for item in result]


def _draw_bead_cell(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    size: int,
    color: Tuple[int, int, int],
) -> None:
    """Render a single bead with rounded rectangle + subtle shadow + highlight."""
    pad = max(1, size // 10)
    r = max(2, size // 4)

    # shadow
    draw.rounded_rectangle(
        [x + pad, y + pad, x + size, y + size],
        radius=r,
        fill=BEAD_SHADOW,
    )
    # bead body
    draw.rounded_rectangle(
        [x, y, x + size - pad, y + size - pad],
        radius=r,
        fill=color,
    )
    # subtle highlight (top-left)
    hl_w = max(1, size // 5)
    hl_h = max(1, size // 5)
    draw.rounded_rectangle(
        [x + pad, y + pad, x + pad + hl_w, y + pad + hl_h],
        radius=hl_w // 2,
        fill=BEAD_HIGHLIGHT,
    )


def _render_grid_image(
    img: Image.Image,
    grid_size: int,
    cell_size: int = 24,
) -> Image.Image:
    """Render the pixel art as a bead grid with individual bead cells."""
    out_w = grid_size * cell_size
    out_h = grid_size * cell_size
    canvas = Image.new("RGBA", (out_w, out_h), (248, 248, 250, 255))
    draw = ImageDraw.Draw(canvas)

    pixels = img.load()
    for row in range(grid_size):
        for col in range(grid_size):
            color = pixels[col, row]  # type: ignore[index]
            x = col * cell_size
            y = row * cell_size
            _draw_bead_cell(draw, x, y, cell_size, color)

    return canvas


def _render_legend(
    palette: List[Tuple[int, int, int]],
    counts: List[int],
    grid_size: int,
    cell_size: int,
) -> Image.Image:
    """Render the colour legend card with total bead count."""
    total = sum(counts)
    swatch = cell_size
    gap_x = 12
    gap_y = 14
    cols = min(len(palette), 6)
    rows = math.ceil(len(palette) / cols)

    font_title = _load_font_bold(15)
    font_item = _load_font(12)
    font_total = _load_font(12)

    card_pad_x = 20
    card_pad_y = 18
    title_h = 28
    total_h = 28

    content_w = cols * (swatch + 64 + gap_x) - gap_x
    card_w = card_pad_x * 2 + content_w
    card_h = card_pad_y * 2 + title_h + rows * (swatch + gap_y) - gap_y + total_h

    legend = Image.new("RGBA", (card_w, card_h), (248, 248, 250, 0))
    draw = ImageDraw.Draw(legend)

    # card background
    draw.rounded_rectangle(
        [0, 0, card_w, card_h],
        radius=14,
        fill=(255, 255, 255, 255),
        outline=(225, 225, 230),
        width=1,
    )

    # title
    draw.text(
        (card_pad_x, card_pad_y),
        "颜色图例 Color Legend",
        fill=TEXT_MAIN,
        font=font_title,
    )

    # swatches
    base_y = card_pad_y + title_h
    for idx, (color, count) in enumerate(zip(palette, counts)):
        r = idx // cols
        c = idx % cols
        x = card_pad_x + c * (swatch + 64 + gap_x)
        y = base_y + r * (swatch + gap_y)

        draw.rounded_rectangle(
            [x, y, x + swatch, y + swatch],
            radius=4,
            fill=color,
            outline=(200, 200, 208),
            width=1,
        )
        pct = count / total * 100 if total else 0
        draw.text(
            (x + swatch + 8, y - 1),
            f"×{count}  ({pct:.1f}%)",
            fill=TEXT_MAIN,
            font=font_item,
        )

    # total row
    total_y = base_y + rows * (swatch + gap_y) - gap_y + 6
    draw.line(
        [(card_pad_x, total_y), (card_w - card_pad_x, total_y)],
        fill=(225, 225, 230),
        width=1,
    )
    draw.text(
        (card_pad_x, total_y + 8),
        f"共 {total:,} 颗拼豆  ·  {grid_size} × {grid_size}  ·  {len(palette)} 色",
        fill=TEXT_SECONDARY,
        font=font_total,
    )

    return legend


def process(
    data: bytes,
    grid_size: int = 32,
    n_colors: int = 24,
    cell_size: int = 24,
) -> Tuple[bytes, dict]:
    """
    Produce a bead-art blueprint from raw image bytes.

    Parameters
    ----------
    data : bytes        Raw JPEG / PNG / WebP bytes.
    grid_size : int     Beads per side.
    n_colors : int      Target colour count.
    cell_size : int     Pixel size of each bead in the output.

    Returns
    -------
    (png_bytes, stats) where stats is:
        {
            "palette": [ [r,g,b], ... ],
            "counts": [int, ...],
            "total": int,
            "grid_size": int,
            "n_colors": int,
        }
    """
    n_colors = min(n_colors, grid_size * grid_size)

    img = _load_image(data)
    img = _resize_preserve(img, grid_size)
    img = _quantize(img, n_colors)
    img = _downsample(img, grid_size)

    palette_raw, counts = _extract_palette(img)
    palette_hex = [[int(c[0]), int(c[1]), int(c[2])] for c in palette_raw]

    grid_img = _render_grid_image(img, grid_size, cell_size)
    legend = _render_legend(palette_raw, counts, grid_size, cell_size)

    # Composite: grid + spacing + legend
    spacer = 24
    final_w = grid_img.width
    final_h = grid_img.height + spacer + legend.height

    canvas = Image.new("RGBA", (final_w, final_h), (248, 248, 250, 255))
    canvas.paste(grid_img, (0, 0), grid_img)
    lx = (final_w - legend.width) // 2
    canvas.paste(legend, (lx, grid_img.height + spacer), legend)

    buf = BytesIO()
    canvas.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    stats = {
        "palette": palette_hex,
        "counts": counts,
        "total": sum(counts),
        "grid_size": grid_size,
        "n_colors": len(palette_hex),
    }

    return png_bytes, stats
