"""
WindowBridge — connects pygame/SDL2 to macOS NSWindow.

Responsibilities:
  - Extract the SDL_Window* from the pygame display
  - Extract the NSWindow* from SDL's WMInfo
  - Apply transparency, floating window level, and all-spaces behaviour
  - Expose position/size/mouse getters and setters used by drag & resize
"""

import ctypes

import pygame

from .constants import SDL2_LIB
from .objc_bridge import (
    cls, send_id, send_long, send_void,
    send_void_bool, send_void_id, send_void_long,
)


class _SDL_version(ctypes.Structure):
    _fields_ = [
        ("major", ctypes.c_uint8),
        ("minor", ctypes.c_uint8),
        ("patch", ctypes.c_uint8),
    ]


class _SDL_SysWMinfo(ctypes.Structure):
    _fields_ = [
        ("version",   _SDL_version),
        ("subsystem", ctypes.c_int),
        ("info",      ctypes.c_uint8 * 64),
    ]


class WindowBridge:
    """
    Bridges SDL2 and the ObjC runtime so that the pygame window behaves
    as a transparent floating overlay without requiring PyObjC AppKit.
    """

    def __init__(self) -> None:
        self._sdl = ctypes.CDLL(SDL2_LIB)
        self._setup_sdl_functions()
        self._sdl_win = self._resolve_sdl_window()
        self._ns_win  = self._resolve_ns_window()
        self._cg_win_id: int = 0  # filled by configure()

    # ── initialisation ────────────────────────────────────────────────────────

    def _resolve_sdl_window(self) -> ctypes.c_void_p:
        """Return the SDL_Window* for the current pygame display."""
        from pygame._sdl2.video import Window as _SDLWin
        sdl_win = _SDLWin.from_display_module()
        self._sdl.SDL_GetWindowFromID.restype  = ctypes.c_void_p
        self._sdl.SDL_GetWindowFromID.argtypes = [ctypes.c_uint32]
        ptr = self._sdl.SDL_GetWindowFromID(ctypes.c_uint32(sdl_win.id))
        if not ptr:
            raise RuntimeError("SDL_GetWindowFromID returned NULL")
        return ctypes.c_void_p(ptr)

    def _resolve_ns_window(self) -> int:
        """Extract the NSWindow* from SDL's platform window info."""
        wminfo = _SDL_SysWMinfo()
        wminfo.version.major = 2
        wminfo.version.minor = 28
        wminfo.version.patch = 3
        ok = self._sdl.SDL_GetWindowWMInfo(self._sdl_win, ctypes.byref(wminfo))
        if not ok:
            raise RuntimeError("SDL_GetWindowWMInfo failed")
        # Cocoa subsystem (4): first 8 bytes of the info union = NSWindow*
        ns_ptr = int.from_bytes(bytes(wminfo.info[:8]), byteorder="little")
        if not ns_ptr:
            raise RuntimeError("NSWindow pointer is NULL")
        return ns_ptr

    def _setup_sdl_functions(self) -> None:
        sdl = self._sdl
        sdl.SDL_GetWindowWMInfo.restype    = ctypes.c_int
        sdl.SDL_GetWindowWMInfo.argtypes   = [ctypes.c_void_p, ctypes.c_void_p]
        sdl.SDL_GetWindowPosition.restype  = None
        sdl.SDL_GetWindowPosition.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        ]
        sdl.SDL_SetWindowPosition.restype  = None
        sdl.SDL_SetWindowPosition.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
        ]
        sdl.SDL_SetWindowSize.restype  = None
        sdl.SDL_SetWindowSize.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
        ]
        sdl.SDL_GetGlobalMouseState.restype  = ctypes.c_uint32
        sdl.SDL_GetGlobalMouseState.argtypes = [
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        ]

    # ── public API ────────────────────────────────────────────────────────────

    def configure(self) -> None:
        """Make the window transparent, floating, and present on all spaces."""
        ns = self._ns_win
        pool = send_id(send_id(cls("NSAutoreleasePool"), "alloc"), "init")
        try:
            send_void_bool(ns, "setOpaque:", False)
            clear = send_id(cls("NSColor"), "clearColor")
            send_void_id(ns,   "setBackgroundColor:", clear)
            send_void_long(ns, "setLevel:", 25)            # NSStatusWindowLevel
            send_void_long(ns, "setCollectionBehavior:", 1 | 16)  # CanJoinAllSpaces | Stationary
            send_void_bool(ns, "setMovable:", False)
            send_void(ns,      "orderFrontRegardless")
            self._cg_win_id = send_long(ns, "windowNumber")
            app = send_id(cls("NSApplication"), "sharedApplication")
            send_void_long(app, "setActivationPolicy:", 0)  # NSApplicationActivationPolicyRegular
        finally:
            send_void(pool, "drain")

    @property
    def cg_window_id(self) -> int:
        return self._cg_win_id

    def get_position(self) -> tuple[int, int]:
        x, y = ctypes.c_int(), ctypes.c_int()
        self._sdl.SDL_GetWindowPosition(self._sdl_win, ctypes.byref(x), ctypes.byref(y))
        return x.value, y.value

    def set_position(self, x: int, y: int) -> None:
        self._sdl.SDL_SetWindowPosition(self._sdl_win, ctypes.c_int(x), ctypes.c_int(y))

    def set_size(self, w: int, h: int) -> None:
        self._sdl.SDL_SetWindowSize(self._sdl_win, ctypes.c_int(w), ctypes.c_int(h))

    def get_global_mouse(self) -> tuple[int, int]:
        x, y = ctypes.c_int(), ctypes.c_int()
        self._sdl.SDL_GetGlobalMouseState(ctypes.byref(x), ctypes.byref(y))
        return x.value, y.value
