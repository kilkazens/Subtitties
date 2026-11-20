"""Subtitle editor – scrollable list of segments with inline editing and dynamic 3-5 word splitting."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

from core.subtitle import SubtitleSegment
from core.i18n import t, i18n
from ui.icons import get_icon


class _SegmentRow(ctk.CTkFrame):
    """Single subtitle row: index | start | end | text | delete."""

    def __init__(
        self,
        master,
        index: int,
        segment: SubtitleSegment,
        on_select: Callable[[int], None],
        on_change: Callable[[], None],
        on_delete: Callable[[int], None],
    ):
        super().__init__(master, fg_color="transparent", corner_radius=10)
        self.idx = index
        self.segment = segment
        self._on_select = on_select
        self._on_change = on_change
        self._selected = False

        # Index badge
        self._lbl_idx = ctk.CTkLabel(
            self, text=f"{index + 1}", width=35, font=("Segoe UI", 11, "bold"), text_color="#818CF8"
        )
        self._lbl_idx.grid(row=0, column=0, padx=(4, 4), pady=4)

        # Start time
        self._entry_start = ctk.CTkEntry(
            self, width=95, height=32, corner_radius=8,
            fg_color="#12131f", border_color="#2a2d46", border_width=1,
            font=("Consolas", 11), placeholder_text="00:00:00,000"
        )
        self._entry_start.insert(0, SubtitleSegment.format_time_srt(segment.start))
        self._entry_start.grid(row=0, column=1, padx=2, pady=4)
        self._entry_start.bind("<FocusOut>", self._save)
        self._entry_start.bind("<Return>", self._save)

        # End time
        self._entry_end = ctk.CTkEntry(
            self, width=95, height=32, corner_radius=8,
            fg_color="#12131f", border_color="#2a2d46", border_width=1,
            font=("Consolas", 11), placeholder_text="00:00:00,000"
        )
        self._entry_end.insert(0, SubtitleSegment.format_time_srt(segment.end))
        self._entry_end.grid(row=0, column=2, padx=2, pady=4)
        self._entry_end.bind("<FocusOut>", self._save)
        self._entry_end.bind("<Return>", self._save)

        # Text
        ph_text = "Subtitle text..." if i18n.get_language() == "en" else "Текст субтитра..."
        self._entry_text = ctk.CTkEntry(
            self, height=32, corner_radius=8,
            fg_color="#12131f", border_color="#2a2d46", border_width=1,
            font=("Segoe UI", 12), placeholder_text=ph_text
        )
        self._entry_text.insert(0, segment.text)
        self._entry_text.grid(row=0, column=3, padx=4, pady=4, sticky="ew")
        self._entry_text.bind("<FocusOut>", self._save)
        self._entry_text.bind("<Return>", self._save)
        self.columnconfigure(3, weight=1)

        # Delete button
        btn_del = ctk.CTkButton(
            self, image=get_icon("cross", size=(12, 12)), text="", width=32, height=30, corner_radius=8,
            fg_color="#381822", hover_color="#EF4444",
            command=lambda: on_delete(self.idx),
        )
        btn_del.grid(row=0, column=4, padx=(2, 6), pady=4)

        # Click to select
        self.bind("<Button-1>", lambda e: self._on_select(self.idx))
        self._lbl_idx.bind("<Button-1>", lambda e: self._on_select(self.idx))

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        color = "#252844" if selected else "transparent"
        self.configure(fg_color=color)

    def _save(self, event=None) -> None:
        self.segment.text = self._entry_text.get()
        self.segment.start = self._parse_time(self._entry_start.get(), self.segment.start)
        self.segment.end = self._parse_time(self._entry_end.get(), self.segment.end)
        self._on_change()

    @staticmethod
    def _parse_time(s: str, fallback: float) -> float:
        """Parse SRT timestamp → seconds."""
        try:
            s = s.strip().replace(",", ".")
            parts = s.split(":")
            if len(parts) == 3:
                h, m, rest = parts
                return int(h) * 3600 + int(m) * 60 + float(rest)
            elif len(parts) == 2:
                m, rest = parts
                return int(m) * 60 + float(rest)
            else:
                return float(s)
        except (ValueError, IndexError):
            return fallback


class SubtitleEditor(ctk.CTkFrame):
    """List editor for subtitle segments with dynamic 3-5 word splitter."""

    def __init__(
        self,
        master,
        on_select: Optional[Callable[[int, SubtitleSegment], None]] = None,
        on_change: Optional[Callable[[], None]] = None,
        **kw,
    ):
        super().__init__(master, fg_color="#161825", corner_radius=16, border_width=1, border_color="#24273d", **kw)
        self._on_select = on_select
        self._on_change = on_change
        self._segments: list[SubtitleSegment] = []
        self._rows: list[_SegmentRow] = []
        self._selected_idx: int = -1

        # ── Header ──
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(hdr, text="📝 Редактор субтитров", font=("Segoe UI", 14, "bold"), text_color="#E2E8F0").pack(side="left")

        btn_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_frame.pack(side="right")

        # Dynamic 3-5 words button
        txt_chunks = " 3-5 Words" if i18n.get_language() == "en" else " 3-5 слов"
        ctk.CTkButton(
            btn_frame, image=get_icon("zap", size=(16, 16)), text=txt_chunks, compound="left",
            width=115, height=32, corner_radius=10,
            fg_color="#F97316", hover_color="#EA580C", font=("Segoe UI", 11, "bold"),
            command=self._split_all_to_dynamic,
        ).pack(side="left", padx=3)

        txt_add = " Add" if i18n.get_language() == "en" else " Добавить"
        ctk.CTkButton(
            btn_frame, image=get_icon("plus", size=(14, 14)), text=txt_add, compound="left",
            width=90, height=32, corner_radius=10,
            fg_color="#22253b", hover_color="#2c304d", font=("Segoe UI", 11),
            command=self._add_new,
        ).pack(side="left", padx=2)

        txt_clear = " Clear" if i18n.get_language() == "en" else " Очистить"
        ctk.CTkButton(
            btn_frame, image=get_icon("trash", size=(14, 14)), text=txt_clear, compound="left",
            width=90, height=32, corner_radius=10,
            fg_color="#22253b", hover_color="#3B1E2B", font=("Segoe UI", 11),
            command=self._clear_all,
        ).pack(side="left", padx=2)

        # ── Column headers ──
        col_hdr = ctk.CTkFrame(self, fg_color="transparent")
        col_hdr.pack(fill="x", padx=10, pady=(4, 0))
        for text, w in [("#", 35), (t("col_start"), 95), (t("col_end"), 95), (t("col_text"), 0), ("", 34)]:
            if w:
                lbl = ctk.CTkLabel(col_hdr, text=text, width=w,
                                   font=("Segoe UI", 11, "bold"), text_color="#64748B")
                lbl.pack(side="left", padx=2)
            else:
                lbl = ctk.CTkLabel(col_hdr, text=text,
                                   font=("Segoe UI", 11, "bold"), text_color="#64748B")
                lbl.pack(side="left", padx=2, fill="x", expand=True)

        # ── Scrollable list ──
        self._scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll_frame.pack(fill="both", expand=True, padx=6, pady=6)

        # Placeholder
        ph_msg = "No subtitles yet.\nClick 🎙 AI Speech-to-Text or ➕ Add." if i18n.get_language() == "en" else "Нет субтитров.\nИспользуйте 🎙 Распознать речь или ➕ Добавить."
        self._placeholder = ctk.CTkLabel(
            self._scroll_frame,
            text=ph_msg,
            text_color="#64748B", font=("Segoe UI", 13),
        )
        self._placeholder.pack(pady=35)

    # ── Public API ───────────────────────────────────────────────

    def set_segments(self, segments: list[SubtitleSegment]) -> None:
        self._segments = segments
        self._selected_idx = -1
        self._rebuild()

    def get_segments(self) -> list[SubtitleSegment]:
        return list(self._segments)

    def select_segment(self, index: int) -> None:
        """Highlight active segment in the editor UI without firing seek or selection callbacks."""
        self._selected_idx = index
        for i, row in enumerate(self._rows):
            row.set_selected(i == index)

    def get_selected_index(self) -> int:
        return self._selected_idx

    # ── Internal ─────────────────────────────────────────────────

    def _split_all_to_dynamic(self) -> None:
        """Split all existing segments into short 3-5 word dynamic chunks."""
        if not self._segments:
            return

        new_segments: list[SubtitleSegment] = []
        for seg in self._segments:
            chunks = seg.split_into_dynamic_chunks(min_words=3, max_words=5)
            new_segments.extend(chunks)

        self._segments = new_segments
        self._rebuild()
        self._notify_change()

    def _rebuild(self) -> None:
        for row in self._rows:
            row.destroy()
        self._rows.clear()

        if self._segments:
            self._placeholder.pack_forget()
        else:
            self._placeholder.pack(pady=35)
            return

        for i, seg in enumerate(self._segments):
            row = _SegmentRow(
                self._scroll_frame, i, seg,
                on_select=self._user_select,
                on_change=self._notify_change,
                on_delete=self._delete,
            )
            row.pack(fill="x", pady=2)
            self._rows.append(row)

    def _user_select(self, index: int) -> None:
        """Triggered ONLY when user explicitly clicks on a row in the table."""
        self.select_segment(index)
        if self._on_select and 0 <= index < len(self._segments):
            self._on_select(index, self._segments[index])

    def _add_new(self) -> None:
        if self._segments:
            last = self._segments[-1]
            start = round(last.end + 0.2, 3)
        else:
            start = 0.0
        seg = SubtitleSegment(start=start, end=round(start + 2.0, 3), text="")
        self._segments.append(seg)
        self._rebuild()
        self.select_segment(len(self._segments) - 1)
        self._notify_change()

    def _delete(self, index: int) -> None:
        if 0 <= index < len(self._segments):
            self._segments.pop(index)
            self._rebuild()
            self._notify_change()

    def _clear_all(self) -> None:
        self._segments.clear()
        self._rebuild()
        self._notify_change()

    def _notify_change(self) -> None:
        if self._on_change:
            self._on_change()
