"""
Screen capture using CGWindowListCreateImage.

The key flag kCGWindowListOptionOnScreenBelowWindow tells macOS to capture
only windows that are *below* our window in Z-order, so our own overlay is
automatically excluded from the image.

CGWindowListCreateImage uses top-left origin (same as SDL), so SDL window
coordinates can be passed to CGRectMake directly with no Y-axis conversion.
"""

import numpy as np
from Quartz import (
    CGDataProviderCopyData,
    CGImageGetBytesPerRow,
    CGImageGetDataProvider,
    CGImageGetHeight,
    CGImageGetWidth,
    CGRectMake,
    CGWindowListCreateImage,
    kCGWindowImageNominalResolution,
    kCGWindowListOptionOnScreenBelowWindow,
)


def capture_rect(
    x: int,
    y: int,
    w: int,
    h: int,
    cg_window_id: int,
) -> np.ndarray | None:
    """
    Capture the screen region (x, y, w, h) excluding the window identified
    by cg_window_id and all windows above it.

    Returns an RGB uint8 array of shape (h, w, 3), or None if the capture
    fails (e.g. Screen Recording permission not granted).
    """
    if w <= 0 or h <= 0:
        return None

    cgimg = CGWindowListCreateImage(
        CGRectMake(x, y, w, h),
        kCGWindowListOptionOnScreenBelowWindow,
        cg_window_id,
        kCGWindowImageNominalResolution,
    )
    if cgimg is None:
        return None

    img_w = CGImageGetWidth(cgimg)
    img_h = CGImageGetHeight(cgimg)
    if img_w == 0 or img_h == 0:
        return None

    bpr  = CGImageGetBytesPerRow(cgimg)
    raw  = bytes(CGDataProviderCopyData(CGImageGetDataProvider(cgimg)))
    cols = bpr // 4  # stride may be wider than img_w due to alignment padding

    full = np.frombuffer(raw, dtype=np.uint8).reshape((img_h, cols, 4))
    # BGRA → RGB: reverse first 3 channels and drop alpha
    return np.ascontiguousarray(full[:, :img_w, 2::-1])
