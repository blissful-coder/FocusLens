"""All magic numbers and colours for FocusLens."""

import os

import pygame

# ── Window geometry ────────────────────────────────────────────────────────────

INITIAL_W: int = 800
INITIAL_H: int = 600
MIN_W: int = 400
MIN_H: int = 250
TOPBAR_H: int = 40
BORDER_W: int = 2
RESIZE_HANDLE: int = 8  # px from each edge that counts as a resize zone

# ── Rendering ─────────────────────────────────────────────────────────────────

TARGET_FPS: int = 30

# ── Platform ──────────────────────────────────────────────────────────────────

SDL2_LIB: str = os.path.join(
    os.path.dirname(pygame.__file__), ".dylibs", "libSDL2-2.0.0.dylib"
)

# ── Colours (RGB) ─────────────────────────────────────────────────────────────

COL_BG          = (18,  18,  20)
COL_TOPBAR      = (35,  35,  38)
COL_BORDER      = (70,  70,  78)
COL_BTN         = (58,  58,  65)
COL_BTN_HOVER   = (80,  80,  90)
COL_BTN_ACTIVE  = (55,  120, 200)
COL_BTN_TEXT    = (220, 220, 225)
COL_CLOSE       = (180, 50,  50)
COL_CLOSE_HOVER = (215, 65,  65)
COL_TITLE       = (160, 160, 170)
COL_PERM_TEXT   = (230, 80,  80)
COL_PERM_HINT   = (140, 140, 155)
