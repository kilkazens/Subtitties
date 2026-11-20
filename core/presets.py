"""Ready-made subtitle style presets with trending Reels fonts and karaoke animations."""

from __future__ import annotations

import copy
import json
import os
import shutil
from typing import Optional

from core.subtitle import SubtitleStyle


def register_app_fonts() -> None:
    """Register all bundled fonts in assets/fonts into Windows GDI for Tkinter widgets."""
    if os.name != "nt":
        return
    import ctypes
    fonts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts"))
    if not os.path.exists(fonts_dir):
        return
    gdi32 = ctypes.windll.gdi32
    for fname in os.listdir(fonts_dir):
        if fname.lower().endswith((".ttf", ".otf")):
            p = os.path.join(fonts_dir, fname)
            gdi32.AddFontResourceExW(p, 0x10, 0)


# Curated, beautiful fonts with verified Cyrillic support (Assets + Windows Fonts)
CYRILLIC_FONTS = [
    "Unbounded",
    "Press Start 2P",
    "Geologica",
    "Onest",
    "Russo One",
    "Rubik Mono One",
    "Comfortaa",
    "Golos Text",
    "Dela Gothic One",
    "Montserrat Black",
    "Rubik Black",
    "Oswald Bold",
    "Bebas Neue",
    "Impact",
    "Arial Black",
    "Bahnschrift",
    "Segoe UI Black",
    "Segoe UI",
    "Trebuchet MS",
    "Verdana",
]

PRESETS: dict[str, SubtitleStyle] = {
    "🔥 Dela Gothic Street (Reels #1)": SubtitleStyle(
        font_name="Dela Gothic One",
        font_size=60,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=4.5,
        shadow_offset=0.0,
        bold=True,
        alignment=2,
        position_x=0.50,
        position_y=0.82,
        max_width_ratio=0.78,
        uppercase=True,
        karaoke_mode="pill_bounce",
        highlight_bg="#FFE600",
        highlight_text_color="#000000",
    ),
    "⚡ Unbounded Neon (Cyberpunk)": SubtitleStyle(
        font_name="Unbounded",
        font_size=54,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=3.5,
        shadow_offset=0.0,
        bold=True,
        alignment=2,
        position_x=0.50,
        position_y=0.84,
        max_width_ratio=0.76,
        uppercase=True,
        karaoke_mode="bounce",
        highlight_color="#00FFF0",
    ),
    "👑 Hormozi Pop (Жёлтая плашка)": SubtitleStyle(
        font_name="Montserrat Black",
        font_size=62,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=4.0,
        shadow_offset=0.0,
        bold=True,
        alignment=2,
        position_x=0.50,
        position_y=0.82,
        max_width_ratio=0.75,
        uppercase=True,
        karaoke_mode="pill_pop",
        highlight_bg="#FFE600",
        highlight_text_color="#000000",
    ),
    "👾 8-Bit Pixel (Press Start 2P)": SubtitleStyle(
        font_name="Press Start 2P",
        font_size=42,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=3.0,
        shadow_offset=2.0,
        bold=False,
        alignment=2,
        position_x=0.50,
        position_y=0.84,
        max_width_ratio=0.82,
        uppercase=True,
        karaoke_mode="bounce",
        highlight_color="#00FF66",
    ),
    "💎 Geologica Modern Rounded": SubtitleStyle(
        font_name="Geologica",
        font_size=58,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=3.5,
        shadow_offset=0.0,
        bold=True,
        alignment=2,
        position_x=0.50,
        position_y=0.84,
        max_width_ratio=0.78,
        uppercase=True,
        karaoke_mode="pill",
        highlight_bg="#6366F1",
        highlight_text_color="#FFFFFF",
    ),
    "✨ Onest Clean Reels": SubtitleStyle(
        font_name="Onest",
        font_size=58,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=3.5,
        shadow_offset=0.0,
        bold=True,
        alignment=2,
        position_x=0.50,
        position_y=0.83,
        max_width_ratio=0.78,
        uppercase=True,
        karaoke_mode="pill_bounce",
        highlight_bg="#FFE600",
        highlight_text_color="#000000",
    ),
    "🚀 Russo One Beast": SubtitleStyle(
        font_name="Russo One",
        font_size=64,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=5.0,
        shadow_offset=0.0,
        bold=True,
        alignment=2,
        position_x=0.50,
        position_y=0.84,
        max_width_ratio=0.78,
        uppercase=True,
        karaoke_mode="color",
        highlight_color="#FFE600",
    ),
    "🧱 Rubik Mono One Block": SubtitleStyle(
        font_name="Rubik Mono One",
        font_size=52,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=4.0,
        shadow_offset=1.0,
        bold=False,
        alignment=2,
        position_x=0.50,
        position_y=0.84,
        max_width_ratio=0.80,
        uppercase=True,
        karaoke_mode="pill",
        highlight_bg="#FF5500",
        highlight_text_color="#FFFFFF",
    ),
    "☁️ Comfortaa Sweet Rounded": SubtitleStyle(
        font_name="Comfortaa",
        font_size=56,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=3.5,
        shadow_offset=0.0,
        bold=True,
        alignment=2,
        position_x=0.50,
        position_y=0.84,
        max_width_ratio=0.78,
        uppercase=True,
        karaoke_mode="pill",
        highlight_bg="#EC4899",
        highlight_text_color="#FFFFFF",
    ),
    "💖 TikTok Neon Pink": SubtitleStyle(
        font_name="Rubik Black",
        font_size=60,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=4.5,
        shadow_offset=0.0,
        bold=True,
        alignment=2,
        position_x=0.50,
        position_y=0.82,
        max_width_ratio=0.75,
        uppercase=True,
        karaoke_mode="pill_bounce",
        highlight_bg="#FF0055",
        highlight_text_color="#FFFFFF",
    ),
    "📱 Tall Reels (Oswald Pop)": SubtitleStyle(
        font_name="Oswald Bold",
        font_size=66,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=4.0,
        shadow_offset=1.5,
        bold=True,
        alignment=2,
        position_x=0.50,
        position_y=0.85,
        max_width_ratio=0.80,
        uppercase=True,
        karaoke_mode="pop",
        highlight_color="#FFE600",
    ),
    "🎬 Bebas Dynamic Caps": SubtitleStyle(
        font_name="Bebas Neue",
        font_size=68,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=4.0,
        shadow_offset=1.0,
        bold=True,
        alignment=2,
        position_x=0.50,
        position_y=0.83,
        max_width_ratio=0.80,
        uppercase=True,
        karaoke_mode="color",
        highlight_color="#FF3B30",
    ),
    "🎬 Classic Impact Bold": SubtitleStyle(
        font_name="Impact",
        font_size=66,
        primary_color="#FFFF00",
        outline_color="#000000",
        outline_width=4.5,
        shadow_offset=0.0,
        bold=True,
        alignment=2,
        position_x=0.50,
        position_y=0.85,
        max_width_ratio=0.80,
        uppercase=True,
        karaoke_mode="pop",
        highlight_color="#FFFFFF",
    ),
    "💬 Subtle Clean White": SubtitleStyle(
        font_name="Golos Text",
        font_size=48,
        primary_color="#FFFFFF",
        outline_color="#000000",
        outline_width=2.5,
        shadow_offset=1.0,
        bold=False,
        alignment=2,
        position_x=0.50,
        position_y=0.86,
        max_width_ratio=0.85,
        uppercase=False,
        karaoke_mode="none",
    ),
}


# ── User Custom Presets & Fonts Storage ───────────────────────────

_USER_PRESETS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "assets", "user_presets.json")
)
_CUSTOM_FONTS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "assets", "custom_fonts.json")
)

_USER_PRESETS: dict[str, SubtitleStyle] = {}


def load_user_presets() -> dict[str, SubtitleStyle]:
    """Load user custom presets from JSON file and merge into PRESETS."""
    global _USER_PRESETS
    if os.path.exists(_USER_PRESETS_FILE):
        try:
            with open(_USER_PRESETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for name, s_dict in data.items():
                    style = SubtitleStyle.from_dict(s_dict)
                    _USER_PRESETS[name] = style
                    PRESETS[name] = style
        except Exception:
            pass
    return _USER_PRESETS


def save_user_preset(name: str, style: SubtitleStyle) -> bool:
    """Save a new or modified user preset permanently to JSON."""
    clean_name = name.strip()
    if not clean_name:
        return False
    # Prefix with a distinctive badge if not present
    if not clean_name.startswith("⭐ "):
        display_name = f"⭐ {clean_name}"
    else:
        display_name = clean_name

    _USER_PRESETS[display_name] = style.copy()
    PRESETS[display_name] = style.copy()

    try:
        data = {k: v.to_dict() for k, v in _USER_PRESETS.items()}
        os.makedirs(os.path.dirname(_USER_PRESETS_FILE), exist_ok=True)
        with open(_USER_PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def delete_user_preset(name: str) -> bool:
    """Delete a user preset from memory and JSON."""
    if name in _USER_PRESETS:
        del _USER_PRESETS[name]
    if name in PRESETS:
        del PRESETS[name]
    try:
        data = {k: v.to_dict() for k, v in _USER_PRESETS.items()}
        with open(_USER_PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def is_user_preset(name: str) -> bool:
    """Check if preset was created by the user."""
    return name in _USER_PRESETS


def get_preset_names() -> list[str]:
    """Return all available preset names, listing user presets first."""
    user_names = list(_USER_PRESETS.keys())
    builtin_names = [k for k in PRESETS.keys() if k not in _USER_PRESETS]
    return user_names + builtin_names


def get_preset(name: str) -> SubtitleStyle:
    """Return a copy of the requested preset, or default."""
    if name in PRESETS:
        return copy.deepcopy(PRESETS[name])
    return copy.deepcopy(PRESETS["🔥 Dela Gothic Street (Reels #1)"])


# ── Custom Fonts Management ──────────────────────────────────────

def import_custom_font(source_path: str) -> tuple[bool, str]:
    """Import a TTF/OTF font file, register it with GDI, and return (success, font_name)."""
    if not os.path.exists(source_path):
        return False, "File does not exist"

    fonts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts"))
    os.makedirs(fonts_dir, exist_ok=True)

    base_name = os.path.basename(source_path)
    dest_path = os.path.join(fonts_dir, base_name)

    # Copy file into assets/fonts if not already there
    if os.path.abspath(source_path) != os.path.abspath(dest_path):
        try:
            shutil.copy2(source_path, dest_path)
        except Exception as e:
            return False, f"Failed to copy font: {e}"

    # Extract true font family name
    font_name = os.path.splitext(base_name)[0]
    try:
        from fontTools.ttLib import TTFont
        tt = TTFont(dest_path)
        for record in tt["name"].names:
            if record.nameID in (1, 4):  # Family or Full name
                font_name = record.toUnicode()
                break
    except Exception:
        pass

    # Register in Windows GDI for Tkinter
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.gdi32.AddFontResourceExW(dest_path, 0x10, 0)
        except Exception:
            pass

    # Add to font list
    if font_name not in CYRILLIC_FONTS:
        CYRILLIC_FONTS.insert(0, font_name)

    # Register in FONT_MAP
    try:
        import ui.video_player as vp
        vp.FONT_MAP[font_name] = dest_path
    except Exception:
        pass

    # Save to custom_fonts.json
    try:
        custom_list: list[dict[str, str]] = []
        if os.path.exists(_CUSTOM_FONTS_FILE):
            with open(_CUSTOM_FONTS_FILE, "r", encoding="utf-8") as f:
                custom_list = json.load(f)
        if not any(entry.get("name") == font_name for entry in custom_list):
            custom_list.append({"name": font_name, "path": dest_path})
            with open(_CUSTOM_FONTS_FILE, "w", encoding="utf-8") as f:
                json.dump(custom_list, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return True, font_name


def load_custom_fonts() -> list[str]:
    """Load previously imported custom fonts from assets/custom_fonts.json."""
    loaded = []
    if os.path.exists(_CUSTOM_FONTS_FILE):
        try:
            with open(_CUSTOM_FONTS_FILE, "r", encoding="utf-8") as f:
                custom_list = json.load(f)
                for entry in custom_list:
                    name = entry.get("name")
                    path = entry.get("path")
                    if name and path and os.path.exists(path):
                        if os.name == "nt":
                            try:
                                import ctypes
                                ctypes.windll.gdi32.AddFontResourceExW(path, 0x10, 0)
                            except Exception:
                                pass
                        if name not in CYRILLIC_FONTS:
                            CYRILLIC_FONTS.insert(0, name)
                        try:
                            import ui.video_player as vp
                            vp.FONT_MAP[name] = path
                        except Exception:
                            pass
                        loaded.append(name)
        except Exception:
            pass
    return loaded


# Automatically load user presets and custom fonts on import
load_user_presets()
load_custom_fonts()
