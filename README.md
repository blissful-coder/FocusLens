# FocusLens

A real-time transparent overlay panel for macOS. Place it over any window — a PDF, a browser, a terminal — and apply live visual effects to whatever is behind it.

![FocusLens Demo](assets/demo.gif)

## Effects

| Button | Effect |
|--------|--------|
| **Invert** | Invert all colours — turns black backgrounds white and vice versa |
| **Blur** | Gaussian blur — obscure sensitive content or reduce visual noise |
| **Zoom** | 1.5× magnification of the centre area |
| **B&W** | Greyscale using standard luminance weights |
| **Normal** | Passthrough — no effect |

## Requirements

- macOS 12 or later
- Python 3.12+
- Dependencies (all installable via pip):

```
pygame>=2.5
numpy>=1.26
Pillow>=10
pyobjc-framework-Quartz
```

Install in one line:

```bash
pip install pygame numpy Pillow pyobjc-framework-Quartz
```

## Usage

```bash
python3 main.py
```

**First launch:** macOS will prompt for Screen Recording permission.
Go to **System Settings → Privacy & Security → Screen Recording**, enable
Terminal (or python3), then relaunch.

### Controls

| Action | How |
|--------|-----|
| Move window | Drag the dark top bar |
| Resize window | Drag any edge or corner |
| Switch effect | Click a button in the top bar |
| Quit | Click **X** or press `Escape` |

## Project structure

```
FocusLens/
├── main.py                  # Entry point
└── focuslens/
    ├── __init__.py
    ├── app.py               # FocusLensApp — main loop, rendering, events
    ├── button.py            # Button widget
    ├── capture.py           # Screen capture via CGWindowListCreateImage
    ├── constants.py         # Window geometry, colours, SDL2 path
    ├── effects.py           # Image effect functions (pure, no side effects)
    ├── objc_bridge.py       # Raw ObjC runtime helpers via ctypes
    └── window_bridge.py     # SDL2 + NSWindow interop
```

## How it works

### Capture

`CGWindowListCreateImage` with the flag `kCGWindowListOptionOnScreenBelowWindow`
captures only windows that are *below* ours in Z-order, automatically excluding
the FocusLens overlay from the screenshot. The captured region maps directly to
the lens area inside the border and top bar.

### Transparency

The pygame window is bridged to macOS `NSWindow` via ctypes and the ObjC
runtime — without importing PyObjC AppKit, which would cause a bus error by
conflicting with SDL's Cocoa window ownership. The bridge sets the window
opaque to `false`, background to `clearColor`, and level to
`NSStatusWindowLevel` (25) so it floats above all other windows.

### Effect pipeline

Each frame: capture → numpy/Pillow effect → blit to pygame surface → draw UI
chrome on top. At 800×600 this runs at ~30 FPS with blur active and faster for
all other effects.

## Troubleshooting

**Black or empty lens area**
The Screen Recording permission has not been granted. Follow the first-launch
instructions above.

**Window appears behind other apps**
The `NSStatusWindowLevel` (25) setting should float above everything. If
another app uses a higher window level (rare), FocusLens may appear behind it.

**SDL2 library not found**
The SDL2 dylib path is resolved automatically from the pygame package location.
If it still fails, verify that pygame is installed and that the dylib exists:

```bash
python3 -c "import pygame, os; print(os.path.join(os.path.dirname(pygame.__file__), '.dylibs', 'libSDL2-2.0.0.dylib'))"
```
