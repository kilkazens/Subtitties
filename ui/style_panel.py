"""Style panel – curated Cyrillic fonts, text boundary slider, presets, and grid controls."""

from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
from typing import Callable, Optional

import customtkinter as ctk

from core.i18n import t, i18n
from core.subtitle import SubtitleStyle
from core.presets import (
    PRESETS,
    CYRILLIC_FONTS,
    get_preset_names,
    get_preset,
    save_user_preset,
    delete_user_preset,
    is_user_preset,
    import_custom_font,
)
from ui.icons import get_icon


class FontPickerDropdown(ctk.CTkFrame):
    """Modern WYSIWYG Font Selector where each font option is rendered in its typeface."""

    def __init__(
        self,
        master,
        fonts: list[str],
        default_font: str = "Unbounded",
        on_change: Optional[Callable[[str], None]] = None,
        **kw,
    ):
        super().__init__(master, fg_color="transparent", **kw)
        self._fonts = fonts
        self._current_font = default_font if default_font in fonts else fonts[0]
        self._on_change = on_change
        self._popup: Optional[ctk.CTkToplevel] = None

        # Main button displaying currently selected font in its own typeface
        self._btn = ctk.CTkButton(
            self,
            text=f"{self._current_font}  ▼",
            font=(self._current_font, 14, "bold"),
            height=42,
            corner_radius=12,
            fg_color="#22253b",
            hover_color="#2c304d",
            border_width=1,
            border_color="#353856",
            anchor="w",
            command=self._toggle_popup,
        )
        self._btn.pack(fill="x")

    def get(self) -> str:
        return self._current_font

    def set(self, font_name: str) -> None:
        if font_name in self._fonts:
            self._current_font = font_name
            try:
                self._btn.configure(
                    text=f"{self._current_font}  ▼",
                    font=(self._current_font, 14, "bold"),
                )
            except Exception:
                self._btn.configure(
                    text=f"{self._current_font}  ▼",
                    font=("Segoe UI", 13, "bold"),
                )

    def update_fonts(self, fonts: list[str]) -> None:
        """Update the list of fonts dynamically."""
        self._fonts = fonts

    def _toggle_popup(self) -> None:
        if self._popup and self._popup.winfo_exists():
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self) -> None:
        self.update_idletasks()
        rx = self._btn.winfo_rootx()
        ry = self._btn.winfo_rooty() + self._btn.winfo_height() + 4
        w = max(310, self._btn.winfo_width())
        h = 360

        self._popup = ctk.CTkToplevel(self)
        self._popup.overrideredirect(True)
        self._popup.geometry(f"{w}x{h}+{rx}+{ry}")
        self._popup.attributes("-topmost", True)
        self._popup.configure(fg_color="#181a28")

        # Container card
        card = ctk.CTkFrame(
            self._popup,
            corner_radius=14,
            fg_color="#181a28",
            border_width=1,
            border_color="#383c5e",
        )
        card.pack(fill="both", expand=True, padx=2, pady=2)

        # Search bar
        search_frame = ctk.CTkFrame(card, fg_color="#12131f", corner_radius=8, border_width=1, border_color="#2a2d46", height=34)
        search_frame.pack(fill="x", padx=10, pady=(8, 4))
        search_frame.pack_propagate(False)

        ctk.CTkLabel(search_frame, image=get_icon("search", size=(14, 14)), text="").pack(side="left", padx=(8, 4), pady=4)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._filter_fonts)
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self._search_var,
            placeholder_text="Поиск шрифта...",
            height=28,
            corner_radius=6,
            fg_color="transparent",
            border_width=0,
            font=("Segoe UI", 12),
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=2)
        search_entry.focus_set()

        # Scrollable list of fonts
        self._list_frame = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            corner_radius=10,
        )
        self._list_frame.pack(fill="both", expand=True, padx=6, pady=(4, 8))

        self._populate_list(self._fonts)

        # Close popup on click outside
        self._popup.bind("<FocusOut>", lambda e: self._check_focus_out())
        self._popup.bind("<Escape>", lambda e: self._close_popup())

    def _check_focus_out(self) -> None:
        if self._popup and self._popup.winfo_exists():
            focus = self._popup.focus_get()
            if focus is None or str(focus).startswith(str(self._popup)) is False:
                self._close_popup()

    def _filter_fonts(self, *args) -> None:
        q = self._search_var.get().lower().strip()
        matched = [f for f in self._fonts if q in f.lower()]
        self._populate_list(matched)

    def _populate_list(self, fonts: list[str]) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()

        if not fonts:
            ctk.CTkLabel(
                self._list_frame,
                text="Шрифт не найден",
                font=("Segoe UI", 12),
                text_color="#888899",
            ).pack(pady=20)
            return

        for fn in fonts:
            is_sel = (fn == self._current_font)
            bg = "#6366F1" if is_sel else "#202338"
            hover = "#4F46E5" if is_sel else "#2c304d"

            item = ctk.CTkFrame(self._list_frame, fg_color=bg, corner_radius=8, height=38)
            item.pack(fill="x", pady=2, padx=4)
            item.pack_propagate(False)

            # Left: Font Name in that font
            lbl_name = ctk.CTkLabel(
                item,
                text=fn,
                font=(fn, 13),
                anchor="w",
                text_color="#FFFFFF",
            )
            lbl_name.pack(side="left", padx=(10, 4), pady=4)

            # Right: Russian sample in that font
            lbl_sample = ctk.CTkLabel(
                item,
                text="Абв 123",
                font=(fn, 11),
                anchor="e",
                text_color="#CBD5E1" if is_sel else "#94A3B8",
            )
            lbl_sample.pack(side="right", padx=(4, 10), pady=4)

            # Click binding
            for widget in (item, lbl_name, lbl_sample):
                widget.bind("<Button-1>", lambda e, f=fn: self._select_font(f))
                widget.bind("<Enter>", lambda e, it=item, sel=is_sel: it.configure(fg_color="#4F46E5" if sel else hover))
                widget.bind("<Leave>", lambda e, it=item, clr=bg: it.configure(fg_color=clr))

    def _select_font(self, font_name: str) -> None:
        self.set(font_name)
        self._close_popup()
        if self._on_change:
            self._on_change(font_name)

    def _close_popup(self) -> None:
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
            self._popup = None


class StylePanel(ctk.CTkFrame):
    """Right sidebar: presets, typography, colors, text boundaries, and positioning."""

    def __init__(
        self,
        master,
        on_style_change: Optional[Callable[[SubtitleStyle], None]] = None,
        on_grid_toggle: Optional[Callable[[bool], None]] = None,
        on_snap_toggle: Optional[Callable[[bool], None]] = None,
        **kw,
    ):
        super().__init__(master, fg_color="#161825", corner_radius=16, border_width=1, border_color="#24273d", **kw)
        self._on_style_change = on_style_change
        self._on_grid_toggle = on_grid_toggle
        self._on_snap_toggle = on_snap_toggle

        self._style = SubtitleStyle()
        self._build_ui()

    # ══════════════════════════════════════════════════════════════
    #  UI construction
    # ══════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        self._tabs = ctk.CTkTabview(
            self,
            corner_radius=14,
            fg_color="#1c1f32",
            segmented_button_selected_color="#6366F1",
            segmented_button_selected_hover_color="#4F46E5",
            segmented_button_unselected_color="#22253b",
            segmented_button_unselected_hover_color="#2c304d",
        )
        self._tabs.pack(fill="both", expand=True, padx=6, pady=6)

        self._t_presets = "🎨 Presets" if i18n.get_language() == "en" else "🎨 Пресеты"
        self._t_style = "⚙️ Typography" if i18n.get_language() == "en" else "⚙️ Шрифт и стиль"
        self._t_karaoke = "🎤 Reels Karaoke" if i18n.get_language() == "en" else "🎤 Караоке / Рилс"
        self._t_position = "📐 Position & Grid" if i18n.get_language() == "en" else "📐 Позиция и сетка"

        self._tabs.add(self._t_presets)
        self._tabs.add(self._t_style)
        self._tabs.add(self._t_karaoke)
        self._tabs.add(self._t_position)

        self._build_presets_tab()
        self._build_style_tab()
        self._build_karaoke_tab()
        self._build_position_tab()

    # ── Presets tab ──────────────────────────────────────────────

    def _build_presets_tab(self) -> None:
        tab = self._tabs.tab(self._t_presets)

        # Save Preset Action Bar
        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x", pady=(4, 8), padx=2)

        ctk.CTkButton(
            bar,
            text=f"💾  {t('save_preset_btn')}",
            image=get_icon("save", size=(16, 16)),
            compound="left",
            height=38,
            corner_radius=10,
            fg_color="#6366F1",
            hover_color="#4F46E5",
            font=("Segoe UI", 12, "bold"),
            command=self._on_save_preset,
        ).pack(fill="x")

        self._presets_grid = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self._presets_grid.pack(fill="both", expand=True)
        self._rebuild_presets_list()

    def _rebuild_presets_list(self) -> None:
        for w in self._presets_grid.winfo_children():
            w.destroy()

        for name in get_preset_names():
            preset = PRESETS.get(name)
            font_fn = preset.font_name if preset else "Segoe UI"
            user_p = is_user_preset(name)

            row = ctk.CTkFrame(self._presets_grid, fg_color="transparent")
            row.pack(fill="x", pady=2, padx=2)

            btn = ctk.CTkButton(
                row,
                text=name,
                height=40,
                corner_radius=10,
                fg_color="#272b44" if user_p else "#22253b",
                hover_color="#363c5e" if user_p else "#2c304d",
                border_width=1,
                border_color="#43486e" if user_p else "#2c2f48",
                font=(font_fn, 12),
                anchor="w",
                command=lambda n=name: self._apply_preset(n),
            )
            btn.pack(side="left", fill="x", expand=True)

            if user_p:
                del_btn = ctk.CTkButton(
                    row,
                    text="",
                    image=get_icon("trash", size=(14, 14)),
                    width=38,
                    height=40,
                    corner_radius=10,
                    fg_color="#3a1d28",
                    hover_color="#5e2436",
                    command=lambda n=name: self._on_delete_preset(n),
                )
                del_btn.pack(side="right", padx=(4, 0))

    def _on_save_preset(self) -> None:
        dialog = ctk.CTkInputDialog(
            text=t("save_preset_dialog_prompt"),
            title=t("save_preset_dialog_title"),
        )
        name = dialog.get_input()
        if name and name.strip():
            save_user_preset(name.strip(), self._style)
            self._rebuild_presets_list()

    def _on_delete_preset(self, name: str) -> None:
        delete_user_preset(name)
        self._rebuild_presets_list()

    def _apply_preset(self, name: str) -> None:
        self._style = get_preset(name)
        self._sync_ui_from_style()
        self._notify()

    # ── Style tab ────────────────────────────────────────────────

    def _build_style_tab(self) -> None:
        tab = self._tabs.tab(self._t_style)
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # WYSIWYG Font Selector + Import Custom Font Button
        font_header = ctk.CTkFrame(scroll, fg_color="transparent")
        font_header.pack(fill="x", pady=(8, 4), padx=5)

        ctk.CTkLabel(
            font_header,
            text=t("font_family_label"),
            font=("Segoe UI", 12, "bold"),
            text_color="#E2E8F0",
        ).pack(side="left")

        btn_add_font = ctk.CTkButton(
            font_header,
            text=f"➕ {t('import_font_btn')}",
            image=get_icon("plus", size=(14, 14)),
            compound="left",
            height=28,
            corner_radius=8,
            fg_color="#22253b",
            hover_color="#2e3250",
            border_width=1,
            border_color="#3b3f63",
            font=("Segoe UI", 11, "bold"),
            command=self._on_import_font,
        )
        btn_add_font.pack(side="right")

        self._font_picker = FontPickerDropdown(
            scroll,
            fonts=CYRILLIC_FONTS,
            default_font="Unbounded",
            on_change=self._on_font_change,
        )
        self._font_picker.pack(fill="x", padx=5)

        # Live Font Preview Card
        self._preview_card = ctk.CTkFrame(scroll, fg_color="#12131f", corner_radius=10, border_width=1, border_color="#272a44")
        self._preview_card.pack(fill="x", padx=5, pady=(8, 6))

        ctk.CTkLabel(self._preview_card, text="👁 Превью шрифта:", font=("Segoe UI", 10, "bold"), text_color="#818CF8").pack(anchor="w", padx=10, pady=(6, 2))
        self._preview_text_lbl = ctk.CTkLabel(
            self._preview_card,
            text="Съешь же ещё этих мягких булок • 123",
            font=("Unbounded", 13),
            text_color="#FFFFFF",
            wraplength=310,
            justify="left",
        )
        self._preview_text_lbl.pack(anchor="w", padx=10, pady=(0, 8))

        # Font size slider
        ctk.CTkLabel(scroll, text="Размер текста:", font=("Segoe UI", 12, "bold"), text_color="#E2E8F0").pack(
            anchor="w", pady=(8, 2), padx=5
        )
        self._size_slider = ctk.CTkSlider(
            scroll, from_=16, to=120, number_of_steps=104, command=self._on_size_change,
            progress_color="#6366F1", button_color="#818CF8", fg_color="#22253b"
        )
        self._size_slider.set(58)
        self._size_slider.pack(fill="x", padx=5)
        self._size_label = ctk.CTkLabel(scroll, text="58 px", font=("Consolas", 11), text_color="#94A3B8")
        self._size_label.pack(anchor="w", padx=5)

        # Formatting flags
        flags = ctk.CTkFrame(scroll, fg_color="transparent")
        flags.pack(fill="x", padx=5, pady=(8, 4))

        self._bold_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            flags, text="Жирный", variable=self._bold_var, command=self._on_flag_change,
            fg_color="#6366F1", hover_color="#4F46E5", font=("Segoe UI", 11)
        ).pack(side="left", padx=5)

        self._italic_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            flags, text="Курсив", variable=self._italic_var, command=self._on_flag_change,
            fg_color="#6366F1", hover_color="#4F46E5", font=("Segoe UI", 11)
        ).pack(side="left", padx=5)

        self._upper_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            flags, text="ВЕРХНИЙ", variable=self._upper_var, command=self._on_flag_change,
            fg_color="#6366F1", hover_color="#4F46E5", font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=5)

        # Primary colour
        ctk.CTkLabel(scroll, text="Цвет текста:", font=("Segoe UI", 12, "bold"), text_color="#E2E8F0").pack(
            anchor="w", pady=(10, 2), padx=5
        )
        self._color_btn = ctk.CTkButton(
            scroll, text="█████  #FFFF00", width=200, height=34, corner_radius=10,
            fg_color="#FFFF00", text_color="#000000", font=("Consolas", 12, "bold"),
            command=lambda: self._pick_color("primary"),
        )
        self._color_btn.pack(anchor="w", padx=5)

        # Outline colour
        ctk.CTkLabel(scroll, text="Цвет обводки:", font=("Segoe UI", 12, "bold"), text_color="#E2E8F0").pack(
            anchor="w", pady=(8, 2), padx=5
        )
        self._outline_btn = ctk.CTkButton(
            scroll, text="█████  #000000", width=200, height=34, corner_radius=10,
            fg_color="#000000", text_color="#FFFFFF", font=("Consolas", 12, "bold"),
            command=lambda: self._pick_color("outline"),
        )
        self._outline_btn.pack(anchor="w", padx=5)

        # Outline width
        ctk.CTkLabel(scroll, text="Толщина обводки:", font=("Segoe UI", 12, "bold"), text_color="#E2E8F0").pack(
            anchor="w", pady=(8, 2), padx=5
        )
        self._outline_slider = ctk.CTkSlider(
            scroll, from_=0, to=10, number_of_steps=20, command=self._on_outline_change,
            progress_color="#6366F1", button_color="#818CF8", fg_color="#22253b"
        )
        self._outline_slider.set(4)
        self._outline_slider.pack(fill="x", padx=5)
        self._outline_label = ctk.CTkLabel(scroll, text="4.0", font=("Consolas", 11), text_color="#94A3B8")
        self._outline_label.pack(anchor="w", padx=5)

        # Shadow
        ctk.CTkLabel(scroll, text="Смещение тени:", font=("Segoe UI", 12, "bold"), text_color="#E2E8F0").pack(
            anchor="w", pady=(8, 2), padx=5
        )
        self._shadow_slider = ctk.CTkSlider(
            scroll, from_=0, to=10, number_of_steps=20, command=self._on_shadow_change,
            progress_color="#6366F1", button_color="#818CF8", fg_color="#22253b"
        )
        self._shadow_slider.set(0)
        self._shadow_slider.pack(fill="x", padx=5)
        self._shadow_label = ctk.CTkLabel(scroll, text="0.0", font=("Consolas", 11), text_color="#94A3B8")
        self._shadow_label.pack(anchor="w", padx=5)

        # Background box
        ctk.CTkLabel(scroll, text="Фон-подложка:", font=("Segoe UI", 12, "bold"), text_color="#E2E8F0").pack(
            anchor="w", pady=(10, 2), padx=5
        )
        self._bg_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            scroll, text="Включить фон за текстом", variable=self._bg_var,
            command=self._on_flag_change, fg_color="#6366F1", font=("Segoe UI", 11)
        ).pack(anchor="w", padx=5)

        self._bg_color_btn = ctk.CTkButton(
            scroll, text="█████  #000000", width=200, height=34, corner_radius=10,
            fg_color="#000000", text_color="#FFFFFF", font=("Consolas", 12, "bold"),
            command=lambda: self._pick_color("background"),
        )
        self._bg_color_btn.pack(anchor="w", padx=5, pady=(4, 0))

        ctk.CTkLabel(scroll, text="Прозрачность фона:", font=("Segoe UI", 11), text_color="#94A3B8").pack(
            anchor="w", pady=(6, 2), padx=5
        )
        self._bg_opacity_slider = ctk.CTkSlider(
            scroll, from_=0, to=1.0, number_of_steps=20, command=self._on_bg_opacity,
            progress_color="#6366F1", button_color="#818CF8", fg_color="#22253b"
        )
        self._bg_opacity_slider.set(0.70)
        self._bg_opacity_slider.pack(fill="x", padx=5)

    # ── Karaoke tab ──────────────────────────────────────────────

    def _build_karaoke_tab(self) -> None:
        tab = self._tabs.tab(self._t_karaoke)
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll, text="🔥 Трендовые анимации слов (Shorts/Reels):",
            font=("Segoe UI", 13, "bold"), text_color="#E2E8F0",
        ).pack(anchor="w", pady=(8, 4), padx=5)

        self._karaoke_modes = {
            "📦 Плашка (Hormozi / CapCut)": "pill",
            "🦘 Подпрыг слова (Bounce)": "bounce",
            "💥 Плавное увеличение (Pop)": "pop",
            "📦🦘 Плашка с подпрыгом": "pill_bounce",
            "📦💥 Плашка + Увеличение": "pill_pop",
            "🌊 Волна по словам (Wave)": "wave",
            "✨ Яркий цвет (Static)": "color",
            "❌ Без анимации (Статика)": "none",
        }
        self._karaoke_mode_rev = {v: k for k, v in self._karaoke_modes.items()}

        self._karaoke_combo = ctk.CTkComboBox(
            scroll,
            values=list(self._karaoke_modes.keys()),
            command=self._on_karaoke_mode_change,
            width=280,
            height=36,
            corner_radius=10,
            fg_color="#22253b",
            border_color="#353856",
        )
        self._karaoke_combo.set("📦 Плашка (Hormozi / CapCut)")
        self._karaoke_combo.pack(fill="x", padx=5, pady=(0, 10))

        # Pill background color
        ctk.CTkLabel(scroll, text="Цвет плашки активного слова:", font=("Segoe UI", 12, "bold"), text_color="#E2E8F0").pack(
            anchor="w", pady=(6, 2), padx=5
        )
        self._hi_bg_btn = ctk.CTkButton(
            scroll, text="█████  #FFE600", width=200, height=34, corner_radius=10,
            fg_color="#FFE600", text_color="#000000", font=("Consolas", 12, "bold"),
            command=lambda: self._pick_color("highlight_bg"),
        )
        self._hi_bg_btn.pack(anchor="w", padx=5)

        # Pill text color
        ctk.CTkLabel(scroll, text="Цвет текста внутри плашки:", font=("Segoe UI", 12, "bold"), text_color="#E2E8F0").pack(
            anchor="w", pady=(6, 2), padx=5
        )
        self._hi_txt_btn = ctk.CTkButton(
            scroll, text="█████  #000000", width=200, height=34, corner_radius=10,
            fg_color="#000000", text_color="#FFFFFF", font=("Consolas", 12, "bold"),
            command=lambda: self._pick_color("highlight_text_color"),
        )
        self._hi_txt_btn.pack(anchor="w", padx=5)

        # Highlight text color
        ctk.CTkLabel(scroll, text="Цвет подсветки (режим без плашки):", font=("Segoe UI", 12, "bold"), text_color="#E2E8F0").pack(
            anchor="w", pady=(6, 2), padx=5
        )
        self._hi_color_btn = ctk.CTkButton(
            scroll, text="█████  #FFE600", width=200, height=34, corner_radius=10,
            fg_color="#FFE600", text_color="#000000", font=("Consolas", 12, "bold"),
            command=lambda: self._pick_color("highlight_color"),
        )
        self._hi_color_btn.pack(anchor="w", padx=5)

        # Fast palettes
        ctk.CTkLabel(scroll, text="Быстрые сочетания:", font=("Segoe UI", 12, "bold"), text_color="#E2E8F0").pack(
            anchor="w", pady=(14, 4), padx=5
        )
        palettes_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        palettes_frame.pack(fill="x", padx=5)

        palettes = [
            ("🟡 Hormozi Yellow", "#FFE600", "#000000", "#FFE600"),
            ("💖 Neon Pink", "#FF0055", "#FFFFFF", "#FF0055"),
            ("⚡ Cyan Glow", "#00F2FE", "#000000", "#00F2FE"),
            ("🟢 Emerald Green", "#10B981", "#FFFFFF", "#10B981"),
        ]
        for name, bg, txt, hi in palettes:
            ctk.CTkButton(
                palettes_frame, text=name, height=32, corner_radius=8,
                fg_color="#22253b", hover_color="#2c304d", font=("Segoe UI", 11),
                command=lambda b=bg, t=txt, h=hi: self._apply_palette(b, t, h),
            ).pack(fill="x", pady=2)

    # ── Position & Grid tab ──────────────────────────────────────

    def _build_position_tab(self) -> None:
        tab = self._tabs.tab(self._t_position)
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll, text="📏 Границы текста (Безопасная зона):",
            font=("Segoe UI", 12, "bold"), text_color="#E2E8F0",
        ).pack(anchor="w", pady=(8, 2), padx=5)

        self._boundary_slider = ctk.CTkSlider(
            scroll, from_=50, to=95, number_of_steps=45, command=self._on_boundary_change,
            progress_color="#6366F1", button_color="#818CF8", fg_color="#22253b"
        )
        self._boundary_slider.set(80)
        self._boundary_slider.pack(fill="x", padx=5)
        self._boundary_label = ctk.CTkLabel(scroll, text="80% ширины видео (автоперенос)", font=("Segoe UI", 11), text_color="#94A3B8")
        self._boundary_label.pack(anchor="w", padx=5)

        # Quick placement buttons
        ctk.CTkLabel(scroll, text="Быстрое выравнивание:", font=("Segoe UI", 12, "bold"), text_color="#E2E8F0").pack(
            anchor="w", pady=(12, 4), padx=5
        )
        quick_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        quick_frame.pack(fill="x", padx=5)

        ctk.CTkButton(
            quick_frame, text="⬇️ Внизу (Стандарт 85%)", height=34, corner_radius=8,
            fg_color="#22253b", hover_color="#2c304d", font=("Segoe UI", 11),
            command=lambda: self._set_alignment(2),
        ).pack(fill="x", pady=2)

        ctk.CTkButton(
            quick_frame, text="↔️ По центру экрана", height=34, corner_radius=8,
            fg_color="#22253b", hover_color="#2c304d", font=("Segoe UI", 11),
            command=lambda: self._set_alignment(5),
        ).pack(fill="x", pady=2)

        ctk.CTkButton(
            quick_frame, text="⬆️ Вверху экрана", height=34, corner_radius=8,
            fg_color="#22253b", hover_color="#2c304d", font=("Segoe UI", 11),
            command=lambda: self._set_alignment(8),
        ).pack(fill="x", pady=2)

        # Coordinates sliders
        ctk.CTkLabel(scroll, text="Точная координата X (Горизонталь):", font=("Segoe UI", 11), text_color="#94A3B8").pack(
            anchor="w", pady=(10, 2), padx=5
        )
        self._pos_x_slider = ctk.CTkSlider(
            scroll, from_=10, to=90, number_of_steps=80, command=self._on_pos_slider,
            progress_color="#6366F1", button_color="#818CF8", fg_color="#22253b"
        )
        self._pos_x_slider.set(50)
        self._pos_x_slider.pack(fill="x", padx=5)
        self._pos_x_label = ctk.CTkLabel(scroll, text="X: 50%", font=("Consolas", 11), text_color="#CBD5E1")
        self._pos_x_label.pack(anchor="w", padx=5)

        ctk.CTkLabel(scroll, text="Точная координата Y (Вертикаль):", font=("Segoe UI", 11), text_color="#94A3B8").pack(
            anchor="w", pady=(6, 2), padx=5
        )
        self._pos_y_slider = ctk.CTkSlider(
            scroll, from_=10, to=95, number_of_steps=85, command=self._on_pos_slider,
            progress_color="#6366F1", button_color="#818CF8", fg_color="#22253b"
        )
        self._pos_y_slider.set(85)
        self._pos_y_slider.pack(fill="x", padx=5)
        self._pos_y_label = ctk.CTkLabel(scroll, text="Y: 85%", font=("Consolas", 11), text_color="#CBD5E1")
        self._pos_y_label.pack(anchor="w", padx=5)

    # ══════════════════════════════════════════════════════════════
    #  Event Handlers
    # ══════════════════════════════════════════════════════════════

    def _on_import_font(self) -> None:
        path = filedialog.askopenfilename(
            title=t("import_font_btn"),
            filetypes=[
                ("Font files (*.ttf, *.otf, *.woff2)", "*.ttf;*.otf;*.woff2"),
                ("TrueType Font (*.ttf)", "*.ttf"),
                ("OpenType Font (*.otf)", "*.otf"),
                ("All files (*.*)", "*.*"),
            ],
        )
        if not path:
            return
        ok, font_name = import_custom_font(path)
        if ok:
            self._font_picker.update_fonts(CYRILLIC_FONTS)
            self._font_picker.set(font_name)
            self._on_font_change(font_name)
            messagebox.showinfo(t("import_font_btn"), t("font_imported_toast", name=font_name))
        else:
            messagebox.showerror("Error", font_name)

    def _on_font_change(self, val: str) -> None:
        self._style.font_name = val
        self._update_preview_card()
        self._notify()

    def _update_preview_card(self) -> None:
        """Update live font preview card styled with current style settings."""
        try:
            sample_text = "СЪЕШЬ ЖЕ ЕЩЁ ЭТИХ БУЛОК • 123" if self._style.uppercase else "Съешь же ещё этих мягких булок • 123"
            self._preview_text_lbl.configure(
                text=sample_text,
                font=(self._style.font_name, 13, "bold" if self._style.bold else "normal"),
                text_color=self._style.primary_color,
            )
        except Exception:
            pass

    def _on_size_change(self, val) -> None:
        sz = int(val)
        self._style.font_size = sz
        self._size_label.configure(text=f"{sz} px")
        self._update_preview_card()
        self._notify()

    def _on_outline_change(self, val) -> None:
        w = round(float(val), 1)
        self._style.outline_width = w
        self._outline_label.configure(text=f"{w}")
        self._notify()

    def _on_shadow_change(self, val) -> None:
        s = round(float(val), 1)
        self._style.shadow_offset = s
        self._shadow_label.configure(text=f"{s}")
        self._notify()

    def _on_bg_opacity(self, val) -> None:
        self._style.background_opacity = round(float(val), 2)
        self._notify()

    def _on_boundary_change(self, val) -> None:
        pct = int(val)
        self._style.max_width_ratio = pct / 100.0
        self._boundary_label.configure(text=f"{pct}% ширины видео (автоперенос)")
        self._notify()

    def _on_pos_slider(self, val=None) -> None:
        px = self._pos_x_slider.get() / 100.0
        py = self._pos_y_slider.get() / 100.0
        self._style.position_x = px
        self._style.position_y = py
        self._pos_x_label.configure(text=f"X: {int(px * 100)}%")
        self._pos_y_label.configure(text=f"Y: {int(py * 100)}%")
        self._notify()

    def _on_flag_change(self) -> None:
        self._style.bold = self._bold_var.get()
        self._style.italic = self._italic_var.get()
        self._style.uppercase = self._upper_var.get()
        self._style.background_box = self._bg_var.get()
        self._update_preview_card()
        self._notify()

    def _on_karaoke_mode_change(self, val: str) -> None:
        mode = self._karaoke_modes.get(val, "pill")
        self._style.karaoke_mode = mode
        self._notify()

    def _apply_palette(self, bg: str, txt: str, hi: str) -> None:
        self._style.highlight_bg = bg
        self._style.highlight_text_color = txt
        self._style.highlight_color = hi
        self._hi_bg_btn.configure(text=f"█████  {bg}", fg_color=bg, text_color="#000000" if self._is_light(bg) else "#FFFFFF")
        self._hi_txt_btn.configure(text=f"█████  {txt}", fg_color=txt, text_color="#000000" if self._is_light(txt) else "#FFFFFF")
        self._hi_color_btn.configure(text=f"█████  {hi}", fg_color=hi, text_color="#000000" if self._is_light(hi) else "#FFFFFF")
        self._notify()

    def _set_alignment(self, align: int) -> None:
        self._style.alignment = align
        if align == 2:    # Bottom
            self._style.position_x = 0.50
            self._style.position_y = 0.85
        elif align == 5:  # Middle
            self._style.position_x = 0.50
            self._style.position_y = 0.50
        elif align == 8:  # Top
            self._style.position_x = 0.50
            self._style.position_y = 0.15
        self.update_position_display(self._style.position_x, self._style.position_y)
        self._notify()

    def update_position_display(self, x: float, y: float) -> None:
        self._pos_x_slider.set(int(x * 100))
        self._pos_y_slider.set(int(y * 100))
        self._pos_x_label.configure(text=f"X: {int(x * 100)}%")
        self._pos_y_label.configure(text=f"Y: {int(y * 100)}%")

    def _pick_color(self, which: str) -> None:
        init = {
            "primary": self._style.primary_color,
            "outline": self._style.outline_color,
            "background": self._style.background_color,
            "highlight_bg": getattr(self._style, "highlight_bg", "#FFE600"),
            "highlight_text_color": getattr(self._style, "highlight_text_color", "#000000"),
            "highlight_color": getattr(self._style, "highlight_color", "#FFE600"),
        }.get(which, "#FFFFFF")

        result = colorchooser.askcolor(color=init, title="Выберите цвет")
        if result and result[1]:
            hex_color = result[1].upper()
            if which == "primary":
                self._style.primary_color = hex_color
                self._color_btn.configure(
                    text=f"█████  {hex_color}", fg_color=hex_color,
                    text_color="#000000" if self._is_light(hex_color) else "#FFFFFF",
                )
                self._update_preview_card()
            elif which == "outline":
                self._style.outline_color = hex_color
                self._outline_btn.configure(
                    text=f"█████  {hex_color}", fg_color=hex_color,
                    text_color="#000000" if self._is_light(hex_color) else "#FFFFFF",
                )
            elif which == "background":
                self._style.background_color = hex_color
                self._bg_color_btn.configure(
                    text=f"█████  {hex_color}", fg_color=hex_color,
                    text_color="#000000" if self._is_light(hex_color) else "#FFFFFF",
                )
            elif which == "highlight_bg":
                self._style.highlight_bg = hex_color
                self._hi_bg_btn.configure(
                    text=f"█████  {hex_color}", fg_color=hex_color,
                    text_color="#000000" if self._is_light(hex_color) else "#FFFFFF",
                )
            elif which == "highlight_text_color":
                self._style.highlight_text_color = hex_color
                self._hi_txt_btn.configure(
                    text=f"█████  {hex_color}", fg_color=hex_color,
                    text_color="#000000" if self._is_light(hex_color) else "#FFFFFF",
                )
            elif which == "highlight_color":
                self._style.highlight_color = hex_color
                self._hi_color_btn.configure(
                    text=f"█████  {hex_color}", fg_color=hex_color,
                    text_color="#000000" if self._is_light(hex_color) else "#FFFFFF",
                )
            self._notify()

    # ══════════════════════════════════════════════════════════════
    #  State Synchronization
    # ══════════════════════════════════════════════════════════════

    def set_style(self, style: SubtitleStyle) -> None:
        self._style = style.copy()
        self._sync_ui_from_style()

    def get_style(self) -> SubtitleStyle:
        return self._style.copy()

    def _sync_ui_from_style(self) -> None:
        s = self._style
        if s.font_name in CYRILLIC_FONTS:
            self._font_picker.set(s.font_name)
        else:
            self._font_picker.set("Unbounded")

        self._size_slider.set(s.font_size)
        self._size_label.configure(text=f"{s.font_size} px")
        self._bold_var.set(s.bold)
        self._italic_var.set(s.italic)
        self._upper_var.set(s.uppercase)
        self._outline_slider.set(s.outline_width)
        self._outline_label.configure(text=f"{s.outline_width}")
        self._shadow_slider.set(s.shadow_offset)
        self._shadow_label.configure(text=f"{s.shadow_offset}")
        self._bg_var.set(s.background_box)
        self._bg_opacity_slider.set(s.background_opacity)

        bw = int(getattr(s, "max_width_ratio", 0.80) * 100)
        self._boundary_slider.set(bw)
        self._boundary_label.configure(text=f"{bw}% ширины видео (автоперенос)")

        px = s.position_x if s.position_x is not None else 0.50
        py = s.position_y if s.position_y is not None else 0.85
        self._pos_x_slider.set(int(px * 100))
        self._pos_y_slider.set(int(py * 100))
        self._pos_x_label.configure(text=f"X: {int(px * 100)}%")
        self._pos_y_label.configure(text=f"Y: {int(py * 100)}%")

        self._color_btn.configure(
            text=f"█████  {s.primary_color}", fg_color=s.primary_color,
            text_color="#000000" if self._is_light(s.primary_color) else "#FFFFFF",
        )
        self._outline_btn.configure(
            text=f"█████  {s.outline_color}", fg_color=s.outline_color,
            text_color="#000000" if self._is_light(s.outline_color) else "#FFFFFF",
        )
        self._bg_color_btn.configure(
            text=f"█████  {s.background_color}", fg_color=s.background_color,
            text_color="#000000" if self._is_light(s.background_color) else "#FFFFFF",
        )

        k_mode = getattr(s, "karaoke_mode", "pill")
        combo_text = self._karaoke_mode_rev.get(k_mode, "📦 Плашка (Hormozi / CapCut)")
        self._karaoke_combo.set(combo_text)

        bg = getattr(s, "highlight_bg", "#FFE600")
        self._hi_bg_btn.configure(
            text=f"█████  {bg}", fg_color=bg,
            text_color="#000000" if self._is_light(bg) else "#FFFFFF",
        )
        txt = getattr(s, "highlight_text_color", "#000000")
        self._hi_txt_btn.configure(
            text=f"█████  {txt}", fg_color=txt,
            text_color="#000000" if self._is_light(txt) else "#FFFFFF",
        )
        hi = getattr(s, "highlight_color", "#FFE600")
        self._hi_color_btn.configure(
            text=f"█████  {hi}", fg_color=hi,
            text_color="#000000" if self._is_light(hi) else "#FFFFFF",
        )
        self._update_preview_card()

    def _notify(self) -> None:
        if self._on_style_change:
            self._on_style_change(self._style.copy())

    @staticmethod
    def _is_light(hex_color: str) -> bool:
        h = hex_color.lstrip("#")
        if len(h) < 6:
            return True
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r * 299 + g * 587 + b * 114) / 1000 > 128
