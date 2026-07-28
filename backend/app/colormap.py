"""
Fast nearest-colour lookup using a KD-tree over CIE Lab space,
which is perceptually uniform — Euclidean distance in Lab correlates
far better with human colour perception than RGB distance.
"""

from typing import List, Tuple

from .palettes import BeadColor, get_palette

# ═══════════════════════════════════════════════════════════════════════
# RGB ↔ Lab conversion (D65 illuminant, sRGB)
# ═══════════════════════════════════════════════════════════════════════

def _rgb_to_lab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Convert sRGB (0-255) → CIE L*a*b* (D65)."""
    # linearise
    var_r = _srgb_inv(r / 255.0)
    var_g = _srgb_inv(g / 255.0)
    var_b = _srgb_inv(b / 255.0)

    # to XYZ (D65)
    x = var_r * 0.4124564 + var_g * 0.3575761 + var_b * 0.1804375
    y = var_r * 0.2126729 + var_g * 0.7151522 + var_b * 0.0721750
    z = var_r * 0.0193339 + var_g * 0.1191920 + var_b * 0.9503041

    # XYZ → Lab
    xn, yn, zn = 0.95047, 1.00000, 1.08883
    fx = _lab_f(x / xn)
    fy = _lab_f(y / yn)
    fz = _lab_f(z / zn)

    L = max(0.0, 116.0 * fy - 16.0)
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return L, a, b


def _srgb_inv(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lab_f(t: float) -> float:
    delta = 6.0 / 29.0
    return t ** (1.0 / 3.0) if t > delta ** 3 else t / (3.0 * delta * delta) + 4.0 / 29.0


# ═══════════════════════════════════════════════════════════════════════
# Simple KD-tree for Lab-space nearest-neighbour
# ═══════════════════════════════════════════════════════════════════════

class _KDNode:
    __slots__ = ("point", "index", "left", "right", "axis")
    def __init__(self, point, index, axis, left=None, right=None):
        self.point = point
        self.index = index
        self.axis = axis
        self.left = left
        self.right = right


class ColorMapper:
    """
    Maps arbitrary RGB colours to the nearest bead in a given palette.

    Uses a KD-tree over CIE L*a*b* space for perceptually-accurate matching.
    """

    def __init__(self, brand: str = "artkal"):
        palette = get_palette(brand)
        self.codes   = [p[0] for p in palette]
        self.names   = [p[1] for p in palette]
        self.rgbs    = [(p[2], p[3], p[4]) for p in palette]
        self.lab_pts = [_rgb_to_lab(*rgb) for rgb in self.rgbs]
        self._root   = self._build(list(range(len(self.lab_pts))), 0)

    def _build(self, indices: List[int], depth: int):
        if not indices:
            return None
        axis = depth % 3
        sorted_idx = sorted(indices, key=lambda i: self.lab_pts[i][axis])
        mid = len(sorted_idx) // 2
        return _KDNode(
            self.lab_pts[sorted_idx[mid]],
            sorted_idx[mid],
            axis,
            self._build(sorted_idx[:mid], depth + 1),
            self._build(sorted_idx[mid + 1:], depth + 1),
        )

    def map(self, r: int, g: int, b: int) -> Tuple[str, str, Tuple[int, int, int]]:
        """
        Return (code, name, rgb) of the nearest bead colour.
        """
        target = _rgb_to_lab(r, g, b)
        best_idx, _ = self._nearest(self._root, target, 0)
        return self.codes[best_idx], self.names[best_idx], self.rgbs[best_idx]

    def _nearest(self, node, target, depth):
        if node is None:
            return None, float("inf")
        axis = depth % 3
        d = sum((a - b) ** 2 for a, b in zip(node.point, target))

        diff = target[axis] - node.point[axis]
        if diff < 0:
            nearer, farther = node.left, node.right
        else:
            nearer, farther = node.right, node.left

        best_idx, best_d = self._nearest(nearer, target, depth + 1)
        if d < best_d:
            best_idx, best_d = node.index, d

        # check if we need to search the farther branch
        if diff * diff < best_d:
            cand_idx, cand_d = self._nearest(farther, target, depth + 1)
            if cand_d < best_d:
                best_idx, best_d = cand_idx, cand_d

        return best_idx, best_d


# ── module-level cache (lazy init, thread-safe enough for our single-worker use) ──

_mappers: dict = {}

def get_mapper(brand: str = "artkal") -> ColorMapper:
    """Return a cached ColorMapper for *brand*."""
    key = brand.lower()
    if key not in _mappers:
        _mappers[key] = ColorMapper(key)
    return _mappers[key]
