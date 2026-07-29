"""
Heuristic computer vision — no ML, pure Python + Pillow.

Provides:
  - Skin colour detection (HSV range)
  - Subject localisation (skin + contrast)
  - Smart crop around subject
  - Face-region weight map
  - Adaptive region-based dithering guide
  - Image type classifier (portrait / graphic / landscape)

All designed for <512 MB RAM, ~100 ms overhead on 200×200 images.
"""

from typing import List, Tuple


# ═══════════════════════════════════════════════════════════════════════
# Skin detection (HSV heuristic — covers most ethnicities)
# ═══════════════════════════════════════════════════════════════════════

def _rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
    cmax = max(rn, gn, bn)
    cmin = min(rn, gn, bn)
    delta = cmax - cmin
    if delta == 0:
        h = 0.0
    elif cmax == rn:
        h = 60.0 * (((gn - bn) / delta) % 6)
    elif cmax == gn:
        h = 60.0 * (((bn - rn) / delta) + 2)
    else:
        h = 60.0 * (((rn - gn) / delta) + 4)
    s = 0.0 if cmax == 0 else delta / cmax
    v = cmax
    return h, s, v


def is_skin(r: int, g: int, b: int) -> bool:
    """True if pixel is likely human skin (wide range for diversity)."""
    h, s, v = _rgb_to_hsv(r, g, b)
    # Wide skin hue range
    if not (0 <= h <= 50 or 330 <= h <= 360):
        return False
    # Saturation: not too grey, not too saturated
    if not (0.08 <= s <= 0.75):
        return False
    # Value: not too dark, not pure white
    if not (0.20 <= v <= 0.95):
        return False
    # Additional: RGB must not be pure grey
    if abs(r - g) < 10 and abs(g - b) < 10 and abs(r - b) < 10:
        return False
    return True


def skin_mask(
    pixels: List[Tuple[int, int, int]], w: int, h: int
) -> List[float]:
    """Per-pixel skin probability (0.0–1.0). Simpler pixel → higher confidence."""
    mask = []
    for p in pixels:
        if is_skin(p[0], p[1], p[2]):
            # Higher confidence for pixels near ideal skin tone
            h, s, v = _rgb_to_hsv(p[0], p[1], p[2])
            conf = 1.0 - abs(s - 0.3) * 1.5 - abs(v - 0.65) * 1.5
            mask.append(max(0.3, min(1.0, conf)))
        else:
            mask.append(0.0)
    return mask


# ═══════════════════════════════════════════════════════════════════════
# Subject localisation
# ═══════════════════════════════════════════════════════════════════════

def subject_bbox(
    pixels: List[Tuple[int, int, int]], w: int, h: int
) -> Tuple[int, int, int, int]:
    """
    Find bounding box of the main subject using:
      - Skin detection (if any)
      - Contrast/variance (non-uniform regions = subject)
      - Center bias (subject tends to be central)

    Returns (left, top, right, bottom).
    """
    skin = skin_mask(pixels, w, h)
    total_skin = sum(skin)

    if total_skin > w * h * 0.02:
        # Portrait mode: subject = skin pixels
        weights = skin
    else:
        # Non-portrait: subject = high-variance regions
        weights = []
        for y in range(h):
            for x in range(w):
                i = y * w + x
                p = pixels[i]
                local_sum_r = local_sum_g = local_sum_b = 0.0
                count = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            ni = ny * w + nx
                            local_sum_r += pixels[ni][0]
                            local_sum_g += pixels[ni][1]
                            local_sum_b += pixels[ni][2]
                            count += 1
                if count > 0:
                    dr = p[0] - local_sum_r / count
                    dg = p[1] - local_sum_g / count
                    db = p[2] - local_sum_b / count
                    weights.append(min(1.0, (dr * dr + dg * dg + db * db) / 2000.0))
                else:
                    weights.append(0.0)

    # Weighted centroid
    total_w = sum(weights) or 1.0
    cx = sum(weights[i] * (i % w) for i in range(len(weights))) / total_w
    cy = sum(weights[i] * (i // w) for i in range(len(weights))) / total_w

    # Weighted bounding box
    left, top, right, bottom = w, h, 0, 0
    for i, wt in enumerate(weights):
        if wt > 0.01:
            x, y = i % w, i // w
            if x < left:   left = x
            if x > right:  right = x
            if y < top:    top = y
            if y > bottom: bottom = y

    if left >= right:
        left, top, right, bottom = 0, 0, w, h

    # Expand by 10% margin, clamp
    mw = int((right - left) * 0.10)
    mh = int((bottom - top) * 0.10)
    left   = max(0, left - mw)
    top    = max(0, top - mh)
    right  = min(w, right + mw)
    bottom = min(h, bottom + mh)

    return left, top, right, bottom


# ═══════════════════════════════════════════════════════════════════════
# Face-region weight map
# ═══════════════════════════════════════════════════════════════════════

def face_weight_map(
    pixels: List[Tuple[int, int, int]], w: int, h: int
) -> List[float]:
    """
    Per-pixel importance weight (0.2–1.0).
    - Skin pixels near centre → highest weight (face)
    - Skin pixels near edge → medium weight (hands/arms)
    - Edge pixels everywhere → medium weight (details)
    - Flat background → lowest weight
    """
    skin = skin_mask(pixels, w, h)
    cx, cy = w / 2.0, h / 2.0
    max_dist = max(cx, cy)

    weights = []
    for i, (p, s) in enumerate(zip(pixels, skin)):
        x, y = i % w, i // w
        dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / max_dist
        centre_bonus = 1.0 - dist * 0.5  # 0.5 at edge, 1.0 at centre

        if s > 0.3:
            # Skin: high weight, centre gets extra
            wgt = 0.7 + 0.3 * centre_bonus * s
        else:
            # Non-skin: check if it's an edge
            local_var = 0.0
            count = 0
            for dy in (-2, 0, 2):
                for dx in (-2, 0, 2):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        ni = ny * w + nx
                        local_var += (
                            abs(p[0] - pixels[ni][0])
                            + abs(p[1] - pixels[ni][1])
                            + abs(p[2] - pixels[ni][2])
                        )
                        count += 1
            edge_score = min(1.0, local_var / (count * 30)) if count > 0 else 0
            wgt = 0.2 + 0.4 * edge_score + 0.2 * centre_bonus

        weights.append(max(0.2, min(1.0, wgt)))

    return weights


# ═══════════════════════════════════════════════════════════════════════
# Image type classifier
# ═══════════════════════════════════════════════════════════════════════

def classify_image(
    pixels: List[Tuple[int, int, int]], w: int, h: int
) -> str:
    """
    Returns: 'portrait', 'graphic', 'landscape', or 'logo'
    """
    skin_total = sum(skin_mask(pixels, w, h))
    skin_pct = skin_total / (w * h)

    # Color diversity
    unique = len(set(pixels))
    diversity = unique / (w * h)

    # Saturation
    avg_sat = sum(_rgb_to_hsv(p[0], p[1], p[2])[1] for p in pixels) / len(pixels)

    if skin_pct > 0.05:
        return "portrait"
    elif diversity < 0.05 and avg_sat > 0.3:
        return "logo"
    elif avg_sat > 0.25:
        return "graphic"
    else:
        return "landscape"
