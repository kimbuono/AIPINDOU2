"""
V5 Colour mapper — CIEDE2000 nearest-neighbour over professional bead palettes.

Uses a KD-tree for O(log N) lookups with CIEDE2000 distance metric,
the state-of-the-art perceptual colour difference formula (CIE 142-2001).
"""

from typing import List, Tuple

from .color_engine import rgb_to_lab, ciede2000
from .palettes import BeadColor, get_palette


class _KDNode:
    __slots__ = ("lab", "index", "left", "right", "axis")
    def __init__(self, lab, index, axis, left=None, right=None):
        self.lab = lab
        self.index = index
        self.axis = axis
        self.left = left
        self.right = right


class ColorMapper:
    """
    Maps arbitrary RGB colours to nearest bead colour using CIEDE2000.
    """

    def __init__(self, brand: str = "artkal"):
        palette = get_palette(brand)
        self.codes  = [p[0] for p in palette]
        self.names  = [p[1] for p in palette]
        self.rgbs   = [(p[2], p[3], p[4]) for p in palette]
        self.labs   = [rgb_to_lab(*rgb) for rgb in self.rgbs]
        self._root  = self._build(list(range(len(self.labs))), 0)

    def _build(self, indices: List[int], depth: int):
        if not indices:
            return None
        axis = depth % 3
        sorted_idx = sorted(indices, key=lambda i: self.labs[i][axis])
        mid = len(sorted_idx) // 2
        return _KDNode(
            self.labs[sorted_idx[mid]], sorted_idx[mid], axis,
            self._build(sorted_idx[:mid], depth + 1),
            self._build(sorted_idx[mid + 1:], depth + 1),
        )

    def map(self, r: int, g: int, b: int) -> Tuple[str, str, Tuple[int, int, int]]:
        """Return (code, name, rgb) of nearest bead via CIEDE2000."""
        target = rgb_to_lab(r, g, b)
        best_idx, _ = self._nearest(self._root, target, float("inf"))
        if best_idx is None:
            best_idx = 0
        return self.codes[best_idx], self.names[best_idx], self.rgbs[best_idx]

    def _nearest(self, node, target, best_d):
        if node is None:
            return None, best_d

        # CIEDE2000 distance
        d = ciede2000(*target, *node.lab)

        if d < best_d:
            best_idx, best_d = node.index, d
        else:
            best_idx = None

        diff = target[node.axis] - node.lab[node.axis]
        if diff < 0:
            nearer, farther = node.left, node.right
        else:
            nearer, farther = node.right, node.left

        cand_idx, cand_d = self._nearest(nearer, target, best_d)
        if cand_d < best_d:
            best_idx, best_d = cand_idx, cand_d

        if diff * diff < best_d * 3.0:  # relaxed bound for CIEDE2000 non-Euclidean
            cand_idx, cand_d = self._nearest(farther, target, best_d)
            if cand_d < best_d:
                best_idx, best_d = cand_idx, cand_d

        return best_idx, best_d


_mappers: dict = {}

def get_mapper(brand: str = "artkal") -> ColorMapper:
    key = brand.lower()
    if key not in _mappers:
        _mappers[key] = ColorMapper(key)
    return _mappers[key]
