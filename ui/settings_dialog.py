"""Settings Dialog for Subtitties.
Allows users to switch application language (English/Russian), manage preferences, and view app info.
"""

from __future__ import annotations

import os
from typing import Callable, Optional
import customtkinter as ctk

from core.i18n import i18n, t, LANG_EN, LANG_RU
from ui.icons import get_icon


class SettingsDialog(ctk.CTkToplevel):
    """Modern modal dialog for configuring application preferences."""

    def __init__(
        self,
        parent: ctk.CTk,
        on_language_changed: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.title(t("settings_title"))
        self.geometry("460x380")
        self.resizable(False, False)
        self.configure(fg_color="#0F111A")

        self._parent = parent
        self._on_language_changed = on_language_changed

        # Set window icon if available
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logo.ico"))
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._center_window()

    def _center_window(self) -> None:
        self.update_idletasks()
        pw = self._parent.winfo_width()
        ph = self._parent.winfo_height()
        px = self._parent.winfo_x()
        py = self._parent.winfo_y()

        w = 460
        h = 380
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
        # Header with icon
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 15))

        title_lbl = ctk.CTkLabel(
            header,
            text=f"⚙️ {t('settings_title')}",
            font=("Segoe UI", 20, "bold"),
            text_color="#FFFFFF",
        )
        title_lbl.pack(side="left")

        # Container card
        card = ctk.CTkFrame(self, fg_color="#181B2A", corner_radius=14, border_width=1, border_color="#2D324D")
        card.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Language selection section
        lang_sec = ctk.CTkFrame(card, fg_color="transparent")
        lang_sec.pack(fill="x", padx=18, pady=(18, 12))

        ctk.CTkLabel(
            lang_sec,
            text=f"🌐 {t('language')}:",
            font=("Segoe UI", 14, "bold"),
            text_color="#E2E8F0",
        ).pack(anchor="w", pady=(0, 6))

        cur_lang = i18n.get_language()
        self._lang_var = ctk.StringVar(value="English" if cur_lang == LANG_EN else "Русский")

        lang_options = ["English", "Русский"]
        self._lang_menu = ctk.CTkSegmentedButton(
            lang_sec,
            values=lang_options,
            variable=self._lang_var,
            command=self._on_lang_select,
            height=36,
            corner_radius=10,
            selected_color="#6366F1",
            selected_hover_color="#4F46E5",
            unselected_color="#22253B",
            unselected_hover_color="#2E3250",
            font=("Segoe UI", 12, "bold"),
        )
        self._lang_menu.pack(fill="x")

        # Notice
        self._note_lbl = ctk.CTkLabel(
            lang_sec,
            text=t("language_changed_note"),
            font=("Segoe UI", 11),
            text_color="#94A3B8",
            wraplength=380,
            justify="left",
        )
        self._note_lbl.pack(anchor="w", pady=(8, 0))

        # App Info Section
        info_frame = ctk.CTkFrame(card, fg_color="#111320", corner_radius=10)
        info_frame.pack(fill="x", padx=18, pady=(10, 16))

        ctk.CTkLabel(
            info_frame,
            text="✨ Subtitties v1.0.0",
            font=("Segoe UI", 13, "bold"),
            text_color="#818CF8",
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            info_frame,
            text="AI-powered Reels & TikTok subtitle generator with word-by-word karaoke animations, custom typography, and zero-distortion video preview.",
            font=("Segoe UI", 11),
            text_color="#94A3B8",
            wraplength=370,
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Bottom close button
        btn_close = ctk.CTkButton(
            self,
            text="OK",
            command=self.destroy,
            width=120,
            height=36,
            corner_radius=10,
            fg_color="#6366F1",
            hover_color="#4F46E5",
            font=("Segoe UI", 13, "bold"),
        )
        btn_close.pack(pady=(0, 16))

    def _on_lang_select(self, val: str) -> None:
        lang_code = LANG_EN if val == "English" else LANG_RU
        i18n.set_language(lang_code)
        self._note_lbl.configure(text=t("language_changed_note"))
        if self._on_language_changed:
            self._on_language_changed(lang_code)
