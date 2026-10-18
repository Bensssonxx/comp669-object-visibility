"""All masks are pixel visibility masks: True means visible, never a model attention mask."""
from __future__ import annotations

import hashlib
import numpy as np


def stable_seed(*parts: object) -> int:
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:8], "little")


def visibility_mask(pattern: str, fraction: float, *, size: int = 224, patch: int = 14, seed: int = 0) -> np.ndarray:
    if size % patch or not 0 <= fraction <= 1:
        raise ValueError("Size must be divisible by patch and fraction must be in [0, 1].")
    g = size // patch
    count = round(g * g * fraction)
    if pattern in {"clean", "prefix"}:
        order = np.arange(g * g)
    elif pattern == "suffix":
        order = np.arange(g * g)[::-1]
    elif pattern == "center":
        y, x = np.indices((g, g))
        # Stable row-major tie break; exact budget even for non-square counts.
        order = np.argsort(((y - (g - 1) / 2) ** 2 + (x - (g - 1) / 2) ** 2).ravel(), kind="stable")
    elif pattern == "random":
        order = np.random.default_rng(seed).permutation(g * g)
    else:
        raise ValueError(f"Unknown pattern: {pattern}")
    keep = np.zeros(g * g, dtype=bool)
    keep[order[:count]] = True
    return np.repeat(np.repeat(keep.reshape(g, g), patch, axis=0), patch, axis=1)


def apply_mask(rgb: np.ndarray, visible: np.ndarray, fill: int = 128) -> np.ndarray:
    if rgb.shape[:2] != visible.shape or rgb.shape[-1] != 3:
        raise ValueError("Image and visibility mask must be spatially aligned RGB.")
    out = rgb.copy()
    out[~visible] = fill
    return out


def coverage(trimap: np.ndarray, visible: np.ndarray) -> dict[str, float]:
    if trimap.shape != visible.shape:
        raise ValueError("Trimap and visibility mask must align.")
    if not np.isin(trimap, [1, 2, 3]).all():
        raise ValueError("Oxford trimap must contain only 1=foreground, 2=background, 3=unknown.")
    fg, bg, unknown = trimap == 1, trimap == 2, trimap == 3
    if fg.sum() == 0:
        raise ValueError("Foreground denominator is zero.")
    return {
        "visible_fraction": float(visible.mean()),
        "object_visibility": float(visible[fg].mean()),
        "background_visibility": float(visible[bg].mean()) if bg.any() else float("nan"),
        "object_fraction": float(fg.mean()),
        "unknown_fraction": float(unknown.mean()),
    }


def candidate_square_masks(size: int = 224, patch: int = 14):
    """25 equal-shape, equal-area occluders on a predetermined 5x5 placement grid."""
    g = size // patch
    side = g // 2
    starts = np.linspace(0, g - side, 5).round().astype(int)
    for y in starts:
        for x in starts:
            keep = np.ones((size, size), dtype=bool)
            keep[y * patch:(y + side) * patch, x * patch:(x + side) * patch] = False
            yield f"square_y{y:02d}_x{x:02d}", keep, (int(y), int(x))


def select_pairs(trimap: np.ndarray, *, caliper: float = 0.03):
    """Choose pairs using annotations only, before any model predictions.

    Object contrast: largest visibility difference at equal occluder area/shape.
    Location pair: equal object visibility within caliper, separated occluder centers.
    Absence of common support produces no location pair, not a relaxed threshold.
    """
    candidates = [(name, mask, pos, coverage(trimap, mask)["object_visibility"])
                  for name, mask, pos in candidate_square_masks(trimap.shape[0])]
    ranked = sorted(candidates, key=lambda x: (x[3], x[0]))
    result = [("object_contrast", "low", ranked[0]), ("object_contrast", "high", ranked[-1])]
    eligible = []
    for i, a in enumerate(candidates):
        for b in candidates[i + 1:]:
            distance = float(np.linalg.norm(np.array(a[2]) - np.array(b[2])))
            # >= 4 patches (56 pixels), forecloses trivial neighboring placements.
            if distance >= 4 and abs(a[3] - b[3]) <= caliper:
                eligible.append((distance, -abs(a[3] - b[3]), a[0], b[0], a, b))
    if eligible:
        best = max(eligible, key=lambda p: p[:4])
        result.extend([("visibility_matched", "a", best[-2]), ("visibility_matched", "b", best[-1])])
    return result
