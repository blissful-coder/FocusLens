"""
Thin wrappers around the ObjC runtime via ctypes.

We avoid importing PyObjC's AppKit here because wrapping an existing
NSWindow with PyObjC causes a bus error — PyObjC's memory management
tries to take ownership of SDL's native window object.
"""

import ctypes

_libobjc = ctypes.CDLL("/usr/lib/libobjc.dylib")
_libobjc.sel_registerName.restype  = ctypes.c_void_p
_libobjc.sel_registerName.argtypes = [ctypes.c_char_p]
_libobjc.objc_getClass.restype     = ctypes.c_void_p
_libobjc.objc_getClass.argtypes    = [ctypes.c_char_p]

_msgSend = _libobjc.objc_msgSend


def sel(name: str) -> int:
    return _libobjc.sel_registerName(name.encode())


def cls(name: str) -> int:
    return _libobjc.objc_getClass(name.encode())


def send_void(obj: int, sel_name: str) -> None:
    _msgSend.restype  = None
    _msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    _msgSend(obj, sel(sel_name))


def send_void_bool(obj: int, sel_name: str, value: bool) -> None:
    _msgSend.restype  = None
    _msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool]
    _msgSend(obj, sel(sel_name), value)


def send_void_long(obj: int, sel_name: str, value: int) -> None:
    _msgSend.restype  = None
    _msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
    _msgSend(obj, sel(sel_name), ctypes.c_long(value))


def send_void_id(obj: int, sel_name: str, value: int) -> None:
    _msgSend.restype  = None
    _msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    _msgSend(obj, sel(sel_name), ctypes.c_void_p(value))


def send_id(obj: int, sel_name: str) -> int:
    _msgSend.restype  = ctypes.c_void_p
    _msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    return _msgSend(obj, sel(sel_name))


def send_long(obj: int, sel_name: str) -> int:
    _msgSend.restype  = ctypes.c_long
    _msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    return int(_msgSend(obj, sel(sel_name)))
