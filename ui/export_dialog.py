"""Export dialog – choose format (SRT / ASS / burn into video) and save."""

from __future__ import annotations

import os
import threading
from tkinter import filedialog
from typing import Optional

import customtkinter as ctk

from core.subtitle import SubtitleProject
from core.exporter import export_srt, export_ass, burn_subtitles
from core.i18n import t, i18n
from ui.icons import get_icon


class ExportDialog(ctk.CTkToplevel):
    """Modal-style export dialog."""

    def __init__(self, master, project: SubtitleProject, **kw):
        super().__init__(master, **kw)
        self.title(t("export_dialog_title"))
        self.geometry("500x440")
        self.resizable(False, False)
        self.grab_set()

        self._project = project
        self._exporting = False

        self._build_ui()
        self.after(100, self.lift)

    def _build_ui(self) -> None:
        self.configure(fg_color="#12131f")
        card = ctk.CTkFrame(self, fg_color="#161825", corner_radius=14, border_width=1, border_color="#272a44")
        card.pack(fill="both", expand=True, padx=12, pady=12)

        # ── Format selector ──
        ctk.CTkLabel(card, text=t("export_format_label"), font=("Segoe UI", 14, "bold"), text_color="#E2E8F0").pack(
            pady=(12, 6), padx=16, anchor="w")

        self._format_var = ctk.StringVar(value="video")

        formats = [
            ("video", t("opt_burn_video")),
            ("srt", t("opt_export_srt")),
            ("ass", t("opt_export_ass")),
        ]
        for val, label in formats:
            ctk.CTkRadioButton(
                card, text=label, variable=self._format_var, value=val,
                font=("Segoe UI", 12), fg_color="#6366F1", hover_color="#4F46E5",
            ).pack(padx=24, pady=4, anchor="w")

        # ── Info ──
        sub_count = len(self._project.segments)
        vid_name = os.path.basename(self._project.video_path) if self._project.video_path else "-"
        lbl_info = f"Subtitles: {sub_count}\nVideo: {vid_name}" if i18n.get_language() == "en" else f"Субтитров: {sub_count}\nВидео: {vid_name}"
        self._info = ctk.CTkLabel(
            card,
            text=lbl_info,
            font=("Segoe UI", 11),
            text_color="#94A3B8",
            justify="left",
        )
        self._info.pack(pady=(12, 4), padx=16, anchor="w")

        # ── Progress ──
        self._progress = ctk.CTkProgressBar(card, mode="determinate", progress_color="#6366F1")
        self._progress.set(0)
        self._progress.pack(fill="x", padx=16, pady=(12, 0))

        self._status_label = ctk.CTkLabel(card, text="", font=("Segoe UI", 11), text_color="#A5B4FC")
        self._status_label.pack(pady=(4, 0))

        # ── Buttons ──
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(16, 12))

        txt_cancel = " Cancel" if i18n.get_language() == "en" else " Отмена"
        ctk.CTkButton(
            btn_frame, image=get_icon("cross", size=(12, 12)), text=txt_cancel, compound="left",
            width=95, height=36, corner_radius=10,
            fg_color="#25283f", hover_color="#333758", font=("Segoe UI", 12),
            command=self._cancel,
        ).pack(side="right", padx=4)

        txt_export = " Export" if i18n.get_language() == "en" else " Экспорт"
        self._export_btn = ctk.CTkButton(
            btn_frame, image=get_icon("export", size=(16, 16)), text=txt_export, compound="left",
            width=140, height=36, corner_radius=10,
            fg_color="#6366F1", hover_color="#4F46E5", font=("Segoe UI", 12, "bold"),
            command=self._do_export,
        )
        self._export_btn.pack(side="right", padx=4)

    # ── Export logic ─────────────────────────────────────────────

    def _do_export(self) -> None:
        if self._exporting:
            return
        if not self._project.segments:
            self._status_label.configure(text="⚠️ Нет субтитров для экспорта!", text_color="#FF4444")
            return

        fmt = self._format_var.get()

        # Choose save path
        if fmt == "srt":
            path = filedialog.asksaveasfilename(
                parent=self, title="Сохранить SRT",
                defaultextension=".srt",
                filetypes=[("SRT файлы", "*.srt"), ("Все файлы", "*.*")],
            )
        elif fmt == "ass":
            path = filedialog.asksaveasfilename(
                parent=self, title="Сохранить ASS",
                defaultextension=".ass",
                filetypes=[("ASS файлы", "*.ass"), ("Все файлы", "*.*")],
            )
        elif fmt == "video":
            if not self._project.video_path:
                self._status_label.configure(
                    text="⚠️ Загрузите видео для прожига субтитров!", text_color="#FF4444")
                return
            path = filedialog.asksaveasfilename(
                parent=self, title="Сохранить видео",
                defaultextension=".mp4",
                filetypes=[("MP4 видео", "*.mp4"), ("Все файлы", "*.*")],
            )
        else:
            return

        if not path:
            return

        self._exporting = True
        self._export_btn.configure(state="disabled")

        if fmt == "video":
            threading.Thread(target=self._export_video, args=(path,), daemon=True).start()
        else:
            self._export_simple(fmt, path)

    def _export_simple(self, fmt: str, path: str) -> None:
        try:
            if fmt == "srt":
                export_srt(self._project.segments, path)
            elif fmt == "ass":
                export_ass(
                    self._project.segments,
                    self._project.style,
                    path,
                    self._project.video_width,
                    self._project.video_height,
                )
            self._progress.set(1.0)
            self._status_label.configure(text=f"✅ Сохранено: {os.path.basename(path)}", text_color="#44CC44")
        except Exception as e:
            self._status_label.configure(text=f"❌ Ошибка: {e}", text_color="#FF4444")
        finally:
            self._exporting = False
            self._export_btn.configure(state="normal")

    def _export_video(self, path: str) -> None:
        import tempfile
        tmp_ass = None
        try:
            # First export ASS to temp file
            tmp_ass = tempfile.NamedTemporaryFile(suffix=".ass", delete=False)
            tmp_ass.close()
            export_ass(
                self._project.segments,
                self._project.style,
                tmp_ass.name,
                self._project.video_width,
                self._project.video_height,
            )

            def progress_cb(frac: float, msg: str) -> None:
                self.after(0, self._progress.set, frac)
                self.after(0, self._status_label.configure, {"text": msg})

            burn_subtitles(
                self._project.video_path,
                tmp_ass.name,
                path,
                progress_callback=progress_cb,
            )

            self.after(0, self._status_label.configure, {
                "text": f"✅ Видео сохранено: {os.path.basename(path)}",
                "text_color": "#44CC44",
            })
            self.after(0, self._progress.set, 1.0)

        except Exception as e:
            self.after(0, self._status_label.configure, {
                "text": f"❌ Ошибка: {e}",
                "text_color": "#FF4444",
            })
        finally:
            self._exporting = False
            self.after(0, self._export_btn.configure, {"state": "normal"})
            if tmp_ass:
                try:
                    os.unlink(tmp_ass.name)
                except OSError:
                    pass

    def _cancel(self) -> None:
        if not self._exporting:
            self.destroy()
