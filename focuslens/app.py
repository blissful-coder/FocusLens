"""
FocusLensApp — the main application class.

Owns the pygame event loop, coordinates capture → effect → render each
frame, and handles dragging and resizing through the WindowBridge.
"""

import sys

import numpy as np
import pygame
import pygame.surfarray
from PIL import Image

from .button import Button
from .capture import capture_rect
from .constants import (
    BORDER_W, COL_BG, COL_BORDER, COL_PERM_HINT,
    COL_PERM_TEXT, COL_TITLE, COL_TOPBAR,
    INITIAL_H, INITIAL_W, MIN_H, MIN_W,
    RESIZE_HANDLE, TARGET_FPS, TOPBAR_H,
)
from .effects import EFFECTS
from .window_bridge import WindowBridge

# Buttons in right-to-left layout order (first entry ends up rightmost)
_BUTTON_DEFS = [
    ("X",      "close",  28),
    ("Normal", "normal", 58),
    ("B&W",    "bw",     46),
    ("Zoom",   "zoom",   46),
    ("Blur",   "blur",   46),
    ("Invert", "invert", 54),
]


class FocusLensApp:
    def __init__(self) -> None:
        self.win_w = INITIAL_W
        self.win_h = INITIAL_H

        self.screen: pygame.Surface | None = None
        self.clock  = pygame.time.Clock()
        self.font_small: pygame.font.Font | None = None
        self.font_title: pygame.font.Font | None = None

        self.active_effect: str = "normal"
        self.buttons: list[Button] = []
        self.bridge: WindowBridge | None = None

        self._dragging = False
        self._drag_offset: tuple[int, int] = (0, 0)

        self._resizing = False
        self._resize_edge: str | None = None
        self._resize_start_global: tuple[int, int] = (0, 0)
        self._resize_start_win: tuple[int, int, int, int] = (0, 0, 0, 0)

    # ── setup ─────────────────────────────────────────────────────────────────

    def setup(self) -> None:
        # pygame.init() MUST come before any ObjC/NSWindow calls
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(
            (self.win_w, self.win_h), pygame.NOFRAME
        )
        pygame.display.set_caption("FocusLens")
        self.font_small = pygame.font.SysFont("helveticaneue", 12)
        self.font_title = pygame.font.SysFont("helveticaneue", 13, bold=True)

        self.bridge = WindowBridge()
        self.bridge.configure()
        self.buttons = [Button(*d) for d in _BUTTON_DEFS]
        self._set_active_effect("normal")

    # ── effect state ──────────────────────────────────────────────────────────

    def _set_active_effect(self, effect_id: str) -> None:
        self.active_effect = effect_id
        for btn in self.buttons:
            btn.is_active = btn.effect_id == effect_id and effect_id != "close"

    # ── capture + effect pipeline ─────────────────────────────────────────────

    def _capture(self) -> np.ndarray | None:
        wx, wy = self.bridge.get_position()
        return capture_rect(
            x=wx + BORDER_W,
            y=wy + TOPBAR_H,
            w=self.win_w - 2 * BORDER_W,
            h=self.win_h - TOPBAR_H - BORDER_W,
            cg_window_id=self.bridge.cg_window_id,
        )

    def _apply_effect(self, rgb: np.ndarray) -> np.ndarray:
        return EFFECTS.get(self.active_effect, EFFECTS["normal"])(rgb)

    # ── drag & resize ─────────────────────────────────────────────────────────

    def _resize_edge_at(self, mx: int, my: int) -> str | None:
        r = RESIZE_HANDLE
        left   = mx < r
        right  = mx >= self.win_w - r
        top    = my < r
        bottom = my >= self.win_h - r
        if top    and left:  return "nw"
        if top    and right: return "ne"
        if bottom and left:  return "sw"
        if bottom and right: return "se"
        if top:    return "n"
        if bottom: return "s"
        if left:   return "w"
        if right:  return "e"
        return None

    def _start_drag(self) -> None:
        self._dragging = True
        gx, gy = self.bridge.get_global_mouse()
        wx, wy = self.bridge.get_position()
        self._drag_offset = (gx - wx, gy - wy)

    def _update_drag(self) -> None:
        gx, gy = self.bridge.get_global_mouse()
        self.bridge.set_position(
            gx - self._drag_offset[0],
            gy - self._drag_offset[1],
        )

    def _start_resize(self, edge: str) -> None:
        self._resizing = True
        self._resize_edge = edge
        self._resize_start_global = self.bridge.get_global_mouse()
        wx, wy = self.bridge.get_position()
        self._resize_start_win = (wx, wy, self.win_w, self.win_h)

    def _update_resize(self) -> None:
        gx, gy = self.bridge.get_global_mouse()
        dx = gx - self._resize_start_global[0]
        dy = gy - self._resize_start_global[1]
        ox, oy, ow, oh = self._resize_start_win
        nx, ny, nw, nh = ox, oy, ow, oh
        edge = self._resize_edge

        if "e" in edge:
            nw = max(MIN_W, ow + dx)
        if "s" in edge:
            nh = max(MIN_H, oh + dy)
        if "w" in edge:
            nw = max(MIN_W, ow - dx)
            nx = ox + (ow - nw)
        if "n" in edge:
            nh = max(MIN_H, oh - dy)
            ny = oy + (oh - nh)

        if nw != self.win_w or nh != self.win_h:
            self.win_w, self.win_h = nw, nh
            self.bridge.set_position(nx, ny)
            self.bridge.set_size(nw, nh)
            self.screen = pygame.display.set_mode((nw, nh), pygame.NOFRAME)

    # ── rendering ─────────────────────────────────────────────────────────────

    def _layout_buttons(self) -> None:
        btn_h   = 24
        btn_top = (TOPBAR_H - btn_h) // 2
        gap     = 6
        x = self.win_w - gap
        for btn in self.buttons:
            x -= btn.width
            btn.update_rect(x, btn_top, btn_h)
            x -= gap

    def _draw_chrome(self) -> None:
        """Draw topbar, title, border, and buttons over the lens content."""
        # Topbar background
        pygame.draw.rect(
            self.screen, COL_TOPBAR,
            pygame.Rect(BORDER_W, BORDER_W,
                        self.win_w - 2 * BORDER_W,
                        TOPBAR_H - BORDER_W),
        )
        # Title
        title = self.font_title.render("FocusLens", True, COL_TITLE)
        self.screen.blit(title, (14, (TOPBAR_H - title.get_height()) // 2))
        # Border
        pygame.draw.rect(
            self.screen, COL_BORDER,
            pygame.Rect(0, 0, self.win_w, self.win_h),
            width=BORDER_W,
        )
        # Buttons
        self._layout_buttons()
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.draw(self.screen, self.font_small, btn.rect.collidepoint(mouse_pos))

    def _render_frame(self, rgb: np.ndarray) -> None:
        lens_w = self.win_w - 2 * BORDER_W
        lens_h = self.win_h - TOPBAR_H - BORDER_W

        fh, fw = rgb.shape[:2]
        if fw != lens_w or fh != lens_h:
            rgb = np.array(
                Image.fromarray(rgb, "RGB").resize((lens_w, lens_h), Image.BILINEAR)
            )

        surf = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
        self.screen.blit(surf, (BORDER_W, TOPBAR_H))
        self._draw_chrome()

    def _render_no_permission(self) -> None:
        self.screen.fill(COL_BG)
        self._draw_chrome()
        lines = [
            ("Screen Recording permission required.", COL_PERM_TEXT),
            ("", None),
            ("System Settings → Privacy & Security → Screen Recording", COL_PERM_HINT),
            ("Enable Terminal (or python3), then relaunch.", COL_PERM_HINT),
        ]
        y = TOPBAR_H + 24
        for text, colour in lines:
            if text:
                surf = self.font_small.render(text, True, colour)
                self.screen.blit(surf, (18, y))
            y += 20

    # ── event handling ────────────────────────────────────────────────────────

    def _handle_mousedown(self, mx: int, my: int) -> None:
        # Priority 1: button click
        for btn in self.buttons:
            if btn.rect.collidepoint(mx, my):
                if btn.effect_id == "close":
                    self._quit()
                self._set_active_effect(btn.effect_id)
                return
        # Priority 2: resize zone
        edge = self._resize_edge_at(mx, my)
        if edge:
            self._start_resize(edge)
            return
        # Priority 3: drag via topbar
        if my < TOPBAR_H:
            self._start_drag()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mousedown(*event.pos)

            elif event.type == pygame.MOUSEMOTION:
                if self._dragging:
                    self._update_drag()
                elif self._resizing:
                    self._update_resize()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._dragging = False
                self._resizing = False
                self._resize_edge = None

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._quit()

    # ── main loop ─────────────────────────────────────────────────────────────

    @staticmethod
    def _quit() -> None:
        pygame.quit()
        sys.exit(0)

    def run(self) -> None:
        while True:
            self._handle_events()
            frame = self._capture()
            if frame is not None:
                self._render_frame(self._apply_effect(frame))
            else:
                self._render_no_permission()
            pygame.display.flip()
            self.clock.tick(TARGET_FPS)
