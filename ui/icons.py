"""High-DPI Vector UI Icons for Subtitties matching modern rounded design."""

from __future__ import annotations

import os
from typing import Optional
from PIL import Image, ImageDraw
import customtkinter as ctk

_ICONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons"))
_ICON_CACHE: dict[tuple[str, int, int, str], ctk.CTkImage] = {}


def _create_base(size=128):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _draw_play(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    pts = [(42, 28), (102, 64), (42, 100)]
    d.polygon(pts, fill=color)
    return im


def _draw_pause(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.rounded_rectangle([34, 26, 54, 102], radius=8, fill=color)
    d.rounded_rectangle([74, 26, 94, 102], radius=8, fill=color)
    return im


def _draw_step_back(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.rounded_rectangle([24, 30, 36, 98], radius=4, fill=color)
    d.polygon([(96, 32), (44, 64), (96, 96)], fill=color)
    return im


def _draw_step_forward(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.rounded_rectangle([92, 30, 104, 98], radius=4, fill=color)
    d.polygon([(32, 32), (84, 64), (32, 96)], fill=color)
    return im


def _draw_restart(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.arc([26, 26, 102, 102], start=50, end=330, fill=color, width=12)
    d.polygon([(64, 8), (64, 44), (36, 26)], fill=color)
    return im


def _draw_rotate(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.arc([26, 26, 102, 102], start=210, end=490, fill=color, width=12)
    d.polygon([(64, 8), (64, 44), (92, 26)], fill=color)
    return im


def _draw_volume_high(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.polygon([(20, 48), (42, 48), (68, 26), (68, 102), (42, 80), (20, 80)], fill=color)
    d.arc([46, 38, 92, 90], start=-55, end=55, fill=color, width=10)
    d.arc([40, 20, 114, 108], start=-55, end=55, fill=color, width=10)
    return im


def _draw_volume_low(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.polygon([(20, 48), (42, 48), (68, 26), (68, 102), (42, 80), (20, 80)], fill=color)
    d.arc([46, 38, 92, 90], start=-55, end=55, fill=color, width=10)
    return im


def _draw_volume_mute(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.polygon([(20, 48), (42, 48), (68, 26), (68, 102), (42, 80), (20, 80)], fill=color)
    d.line([(82, 48), (110, 80)], fill=color, width=10)
    d.line([(110, 48), (82, 80)], fill=color, width=10)
    return im


def _draw_grid(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    r = 6
    d.rounded_rectangle([22, 22, 58, 58], radius=r, outline=color, width=10)
    d.rounded_rectangle([70, 22, 106, 58], radius=r, outline=color, width=10)
    d.rounded_rectangle([22, 70, 58, 106], radius=r, outline=color, width=10)
    d.rounded_rectangle([70, 70, 106, 106], radius=r, outline=color, width=10)
    return im


def _draw_magnet(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.arc([26, 26, 102, 102], start=0, end=180, fill=color, width=22)
    d.rectangle([26, 26, 48, 64], fill=color)
    d.rectangle([80, 26, 102, 64], fill=color)
    d.line([(24, 40), (50, 40)], fill=(0, 0, 0, 255), width=4)
    d.line([(78, 40), (104, 40)], fill=(0, 0, 0, 255), width=4)
    return im


def _draw_folder(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.rounded_rectangle([20, 28, 60, 48], radius=6, fill=color)
    d.rounded_rectangle([20, 40, 108, 100], radius=10, fill=color)
    return im


def _draw_folder_open(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.rounded_rectangle([20, 24, 60, 44], radius=6, fill=color)
    d.rounded_rectangle([20, 36, 104, 96], radius=8, outline=color, width=8)
    d.polygon([(16, 96), (32, 54), (116, 54), (100, 96)], fill=color)
    return im


def _draw_mic(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.rounded_rectangle([48, 20, 80, 72], radius=16, fill=color)
    d.arc([36, 36, 92, 92], start=0, end=180, fill=color, width=10)
    d.line([(64, 92), (64, 108)], fill=color, width=10)
    d.line([(44, 108), (84, 108)], fill=color, width=10)
    return im


def _draw_file_text(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.rounded_rectangle([30, 20, 98, 108], radius=8, outline=color, width=10)
    d.line([(44, 46), (84, 46)], fill=color, width=8)
    d.line([(44, 64), (84, 64)], fill=color, width=8)
    d.line([(44, 82), (72, 82)], fill=color, width=8)
    return im


def _draw_export(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.line([(24, 68), (24, 104), (104, 104), (104, 68)], fill=color, width=10)
    d.line([(64, 82), (64, 24)], fill=color, width=10)
    d.polygon([(64, 16), (42, 44), (86, 44)], fill=color)
    return im


def _draw_save(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.rounded_rectangle([24, 24, 104, 104], radius=10, fill=color)
    d.rectangle([42, 24, 86, 54], fill=(22, 24, 37, 255))
    d.rectangle([70, 28, 80, 48], fill=color)
    d.rounded_rectangle([36, 68, 92, 100], radius=4, fill=(22, 24, 37, 255))
    return im


def _draw_zap(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    pts = [(74, 16), (36, 68), (62, 68), (54, 112), (92, 60), (66, 60)]
    d.polygon(pts, fill=color)
    return im


def _draw_plus(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.rounded_rectangle([56, 26, 72, 102], radius=8, fill=color)
    d.rounded_rectangle([26, 56, 102, 72], radius=8, fill=color)
    return im


def _draw_cross(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.line([(32, 32), (96, 96)], fill=color, width=14)
    d.line([(96, 32), (32, 96)], fill=color, width=14)
    return im


def _draw_trash(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.rounded_rectangle([26, 30, 102, 42], radius=4, fill=color)
    d.rounded_rectangle([50, 20, 78, 30], radius=4, fill=color)
    d.polygon([(34, 46), (94, 46), (86, 106), (42, 106)], fill=color)
    d.line([(52, 56), (50, 96)], fill=(22, 24, 37, 255), width=6)
    d.line([(64, 56), (64, 96)], fill=(22, 24, 37, 255), width=6)
    d.line([(76, 56), (78, 96)], fill=(22, 24, 37, 255), width=6)
    return im


def _draw_search(size=128, color=(255, 255, 255, 255)):
    im, d = _create_base(size)
    d.ellipse([26, 26, 82, 82], outline=color, width=12)
    d.line([(72, 72), (102, 102)], fill=color, width=14)
    return im


def _draw_settings(size=128, color=(255, 255, 255, 255)):
    import math
    im, d = _create_base(size)
    d.ellipse([30, 30, 98, 98], outline=color, width=14)
    for angle in [0, 45, 90, 135]:
        rad = math.radians(angle)
        dx = int(math.cos(rad) * 46)
        dy = int(math.sin(rad) * 46)
        d.line([(64 - dx, 64 - dy), (64 + dx, 64 + dy)], fill=color, width=14)
    d.ellipse([44, 44, 84, 84], fill=color)
    d.ellipse([54, 54, 74, 74], fill=(22, 24, 37, 255))
    return im


_DRAW_FUNCS = {
    "play": _draw_play,
    "pause": _draw_pause,
    "step_back": _draw_step_back,
    "step_forward": _draw_step_forward,
    "restart": _draw_restart,
    "rotate": _draw_rotate,
    "volume_high": _draw_volume_high,
    "volume_low": _draw_volume_low,
    "volume_mute": _draw_volume_mute,
    "grid": _draw_grid,
    "magnet": _draw_magnet,
    "folder": _draw_folder,
    "folder_open": _draw_folder_open,
    "mic": _draw_mic,
    "file_text": _draw_file_text,
    "export": _draw_export,
    "save": _draw_save,
    "zap": _draw_zap,
    "plus": _draw_plus,
    "cross": _draw_cross,
    "trash": _draw_trash,
    "search": _draw_search,
    "settings": _draw_settings,
}


def ensure_icons_generated() -> None:
    """Ensure all vector icons exist on disk."""
    os.makedirs(_ICONS_DIR, exist_ok=True)
    for name, fn in _DRAW_FUNCS.items():
        p = os.path.join(_ICONS_DIR, f"{name}.png")
        if not os.path.exists(p):
            im = fn()
            im.save(p)


def get_icon(name: str, size: tuple[int, int] = (20, 20), color: Optional[str] = None) -> ctk.CTkImage:
    """Return a cached high-DPI CTkImage icon by name."""
    cache_key = (name, size[0], size[1], str(color))
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    path = os.path.join(_ICONS_DIR, f"{name}.png")
    if not os.path.exists(path):
        ensure_icons_generated()

    if os.path.exists(path):
        img = Image.open(path)
    else:
        fn = _DRAW_FUNCS.get(name, _draw_play)
        img = fn()

    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
    _ICON_CACHE[cache_key] = ctk_img
    return ctk_img
