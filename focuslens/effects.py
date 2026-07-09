"""
Image effect functions.

Each function takes an RGB numpy array (H, W, 3) uint8 and returns
a processed array of the same shape. They are pure functions with no
side effects, which makes them easy to test or swap out.
"""

import numpy as np
from PIL import Image, ImageFilter

# Luminance weights (ITU-R BT.601)
_LUM_R = 0.299
_LUM_G = 0.587
_LUM_B = 0.114


def apply_normal(rgb: np.ndarray) -> np.ndarray:
    return rgb


def apply_invert(rgb: np.ndarray) -> np.ndarray:
    return 255 - rgb


def apply_bw(rgb: np.ndarray) -> np.ndarray:
    gray = (
        _LUM_R * rgb[:, :, 0].astype(np.float32)
        + _LUM_G * rgb[:, :, 1].astype(np.float32)
        + _LUM_B * rgb[:, :, 2].astype(np.float32)
    ).astype(np.uint8)
    return np.stack([gray, gray, gray], axis=2)


def apply_blur(rgb: np.ndarray, radius: int = 8) -> np.ndarray:
    return np.array(
        Image.fromarray(rgb, "RGB").filter(ImageFilter.GaussianBlur(radius=radius))
    )


def apply_zoom(rgb: np.ndarray, factor: float = 1.5) -> np.ndarray:
    h, w = rgb.shape[:2]
    zh = max(1, int(h / factor))
    zw = max(1, int(w / factor))
    y0 = (h - zh) // 2
    x0 = (w - zw) // 2
    crop = rgb[y0:y0 + zh, x0:x0 + zw]
    return np.array(Image.fromarray(crop, "RGB").resize((w, h), Image.BILINEAR))


# Map effect_id → function for O(1) dispatch
EFFECTS = {
    "normal": apply_normal,
    "invert": apply_invert,
    "bw":     apply_bw,
    "blur":   apply_blur,
    "zoom":   apply_zoom,
}
