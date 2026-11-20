"""Subtitties – main application window with speech recognition, video preview, audio, presets, and grid positioning."""

from __future__ import annotations

import os
import threading
import time
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from core.subtitle import SubtitleProject, SubtitleSegment, SubtitleStyle
from core.presets import get_preset, register_app_fonts
from core.i18n import t, i18n
from core.recognizer import (
    SpeechRecognizer,
    is_available as whisper_available,
    is_model_cached,
    get_cuda_info,
    MODEL_SIZES,
    MODEL_DESCRIPTIONS,
    LANGUAGES,
)

from ui.video_player import VideoPlayer
from ui.subtitle_editor import SubtitleEditor
from ui.style_panel import StylePanel
from ui.export_dialog import ExportDialog
from ui.settings_dialog import SettingsDialog
from ui.icons import get_icon


# ═══════════════════════════════════════════════════════════════════
#  Recognize Dialog (CUDA/CPU, Models, VAD, Batching, Language)
# ═══════════════════════════════════════════════════════════════════

class RecognizeDialog(ctk.CTkToplevel):
    """Pick device (CUDA/CPU), model, optimizations, and language with clear cache indicators."""

    def __init__(self, master, video_path: str, on_done, **kw):
        super().__init__(master, **kw)
        self.title("🎙 Fast AI Speech-to-Text" if i18n.get_language() == "en" else "🎙 Быстрое распознавание речи")
        self.geometry("600x680")
        self.resizable(False, False)
        self.grab_set()

        self._video_path = video_path
        self._on_done = on_done
        self._running = False

        cuda_available, gpu_name = get_cuda_info()
        self._cuda_available = cuda_available
        self._gpu_name = gpu_name

        self._build_ui()
        self.after(100, self.lift)

    def _build_ui(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=(10, 0))

        # ── 1. Device selection ──
        ctk.CTkLabel(scroll, text="⚡ Устройство для вычислений:", font=("Segoe UI", 14, "bold"), text_color="#E2E8F0").pack(
            pady=(5, 4), anchor="w")

        self._device_var = ctk.StringVar(value="cuda" if self._cuda_available else "cpu")

        dev_frame = ctk.CTkFrame(scroll, fg_color="#1c1f32", corner_radius=12, border_width=1, border_color="#272a44")
        dev_frame.pack(fill="x", pady=(0, 10))

        if self._cuda_available:
            cuda_text = f"🚀 Видеокарта NVIDIA (CUDA) — {self._gpu_name}"
            cuda_radio = ctk.CTkRadioButton(
                dev_frame, text=cuda_text, variable=self._device_var, value="cuda",
                font=("Segoe UI", 12, "bold"), text_color="#55ff88",
                fg_color="#10B981", hover_color="#059669",
            )
            cuda_radio.pack(padx=15, pady=8, anchor="w")
        else:
            ctk.CTkLabel(
                dev_frame, text="⚠️ Видеокарта NVIDIA с CUDA не обнаружена",
                font=("Segoe UI", 11), text_color="#ffbb44",
            ).pack(padx=15, pady=(8, 2), anchor="w")

        cpu_radio = ctk.CTkRadioButton(
            dev_frame, text="💻 Процессор (CPU)", variable=self._device_var, value="cpu",
            font=("Segoe UI", 12), fg_color="#6366F1", hover_color="#4F46E5",
        )
        cpu_radio.pack(padx=15, pady=(2, 8), anchor="w")

        # ── 2. Model selection with Cache tags ──
        ctk.CTkLabel(scroll, text="🧠 Выбор модели распознавания:", font=("Segoe UI", 14, "bold"), text_color="#E2E8F0").pack(
            pady=(5, 4), anchor="w")

        default_model = "small" if is_model_cached("small") else ("base" if is_model_cached("base") else "small")
        self._model_var = ctk.StringVar(value=default_model)

        model_frame = ctk.CTkFrame(scroll, fg_color="#1c1f32", corner_radius=12, border_width=1, border_color="#272a44")
        model_frame.pack(fill="x", pady=(0, 10))

        for size in MODEL_SIZES:
            cached = is_model_cached(size)
            desc = MODEL_DESCRIPTIONS[size]

            row = ctk.CTkFrame(model_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=4)

            ctk.CTkRadioButton(
                row, text=desc, variable=self._model_var, value=size,
                font=("Segoe UI", 12), fg_color="#6366F1", hover_color="#4F46E5",
            ).pack(side="left")

            if cached:
                tag = ctk.CTkLabel(
                    row, text="💾 СКАЧАНА (1 СЕК)", font=("Segoe UI", 10, "bold"),
                    text_color="#00ff88", fg_color="#113322", corner_radius=6,
                    width=130, height=22,
                )
                tag.pack(side="right", padx=5)
            else:
                tag = ctk.CTkLabel(
                    row, text="🌐 1-я загрузка", font=("Segoe UI", 10),
                    text_color="#aaaaaa", fg_color="#282836", corner_radius=6,
                    width=100, height=22,
                )
                tag.pack(side="right", padx=5)

        # ── 3. Optimizations ──
        ctk.CTkLabel(scroll, text="⚙️ Ускорение и оптимизации:", font=("Segoe UI", 14, "bold"), text_color="#E2E8F0").pack(
            pady=(5, 4), anchor="w")

        opt_frame = ctk.CTkFrame(scroll, fg_color="#1c1f32", corner_radius=12, border_width=1, border_color="#272a44")
        opt_frame.pack(fill="x", pady=(0, 10))

        self._vad_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opt_frame,
            text="🤫 VAD-фильтр — вырезать паузы и тишину (ускоряет на 30–50%)",
            variable=self._vad_var, font=("Segoe UI", 12),
            fg_color="#6366F1", hover_color="#4F46E5",
        ).pack(padx=15, pady=6, anchor="w")

        self._dynamic_words_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opt_frame,
            text="⚡ Разделять по 3–5 слов (динамичные субтитры для Shorts/Reels)",
            variable=self._dynamic_words_var, font=("Segoe UI", 12, "bold"), text_color="#ffcc00",
            fg_color="#F97316", hover_color="#EA580C",
        ).pack(padx=15, pady=(0, 6), anchor="w")

        # Compute type
        type_row = ctk.CTkFrame(opt_frame, fg_color="transparent")
        type_row.pack(fill="x", padx=15, pady=(0, 8))
        ctk.CTkLabel(type_row, text="Точность вычислений:", font=("Segoe UI", 11), text_color="#94A3B8").pack(side="left", padx=(0, 8))

        self._compute_var = ctk.StringVar(value="float16" if self._cuda_available else "int8")
        compute_combo = ctk.CTkComboBox(
            type_row, values=["float16", "int8", "float32"], variable=self._compute_var, width=120,
            corner_radius=8, fg_color="#12131f", border_color="#2a2d46",
        )
        compute_combo.pack(side="left")

        # ── 4. Language ──
        ctk.CTkLabel(scroll, text="🌐 Язык аудио:", font=("Segoe UI", 14, "bold"), text_color="#E2E8F0").pack(
            pady=(5, 4), anchor="w")

        lang_names = list(LANGUAGES.values())
        lang_codes = list(LANGUAGES.keys())
        self._lang_combo = ctk.CTkComboBox(
            scroll, values=lang_names, width=320, height=36, corner_radius=10,
            fg_color="#1c1f32", border_color="#272a44",
        )
        self._lang_combo.set(LANGUAGES["ru"])
        self._lang_combo.pack(padx=5, pady=(0, 10), anchor="w")
        self._lang_codes = lang_codes
        self._lang_names = lang_names

        # ── Bottom action area ──
        bottom_frame = ctk.CTkFrame(self, fg_color="#12131f", height=115)
        bottom_frame.pack(fill="x", side="bottom")

        self._progress = ctk.CTkProgressBar(bottom_frame, mode="determinate", progress_color="#6366F1")
        self._progress.set(0)
        self._progress.pack(fill="x", padx=20, pady=(12, 0))

        st_text = "Click Start to begin AI speech recognition" if i18n.get_language() == "en" else "Нажмите кнопку для начала распознавания"
        self._status = ctk.CTkLabel(
            bottom_frame, text=st_text,
            font=("Segoe UI", 12), text_color="#aaaaaa",
        )
        self._status.pack(pady=(4, 0))

        btn = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn.pack(fill="x", padx=20, pady=(6, 12))

        txt_cancel = " Cancel" if i18n.get_language() == "en" else " Отмена"
        ctk.CTkButton(
            btn, image=get_icon("cross", size=(12, 12)), text=txt_cancel, compound="left",
            width=95, height=36, corner_radius=10,
            fg_color="#25283f", hover_color="#333758", font=("Segoe UI", 12),
            command=self._cancel,
        ).pack(side="right", padx=5)

        txt_start = " Start Recognition" if i18n.get_language() == "en" else " Распознать"
        self._start_btn = ctk.CTkButton(
            btn, image=get_icon("mic", size=(16, 16)), text=txt_start, compound="left",
            width=180, height=36, corner_radius=10,
            fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 13, "bold"),
            command=self._start,
        )
        self._start_btn.pack(side="right", padx=5)

    def _start(self) -> None:
        if self._running:
            return
        self._running = True
        self._start_btn.configure(state="disabled")

        model_size = self._model_var.get()
        device = self._device_var.get()
        compute_type = self._compute_var.get()
        vad_filter = self._vad_var.get()
        dynamic_words = self._dynamic_words_var.get()

        lang_idx = self._lang_names.index(self._lang_combo.get())
        lang_code = self._lang_codes[lang_idx]

        self._progress.set(0.02)
        if is_model_cached(model_size):
            self._status.configure(
                text=f"🚀 Модель '{model_size}' найдена на диске! Загрузка в память...",
                text_color="#55ff88",
            )
        else:
            self._status.configure(
                text=f"🌐 Скачивание модели '{model_size}' из сети... Пожалуйста, подождите (1 раз)",
                text_color="#ffbb44",
            )

        threading.Thread(
            target=self._run_recognize,
            args=(model_size, device, compute_type, lang_code, vad_filter, dynamic_words),
            daemon=True,
        ).start()

    def _run_recognize(
        self,
        model_size: str,
        device: str,
        compute_type: str,
        lang: str,
        vad_filter: bool,
        dynamic_words: bool,
    ) -> None:
        try:
            start_time = time.time()

            def status_cb(msg: str):
                self.after(0, self._status.configure, {"text": msg})

            def progress_cb(frac: float, msg: str):
                elapsed = time.time() - start_time
                full_msg = f"{msg} (прошло {elapsed:.0f}с)"
                self.after(0, self._progress.set, frac)
                self.after(0, self._status.configure, {"text": full_msg, "text_color": "#ffffff"})

            rec = SpeechRecognizer(
                model_size=model_size,
                device=device,
                compute_type=compute_type,
                status_callback=status_cb,
            )

            segments = rec.transcribe(
                self._video_path,
                language=lang,
                vad_filter=vad_filter,
                dynamic_words=dynamic_words,
                progress_callback=progress_cb,
            )
            self.after(0, self._finish, segments)
        except Exception as e:
            self.after(0, self._status.configure, {
                "text": f"❌ Ошибка: {e}", "text_color": "#FF4444"
            })
            self.after(0, self._start_btn.configure, {"state": "normal"})
            self._running = False

    def _finish(self, segments: list[SubtitleSegment]) -> None:
        self._on_done(segments)
        self.destroy()

    def _cancel(self) -> None:
        if not self._running:
            self.destroy()


# ═══════════════════════════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════════════════════════

class SubtittiesApp(ctk.CTk):
    """Root application window for Subtitties."""

    APP_TITLE = "🎬 Subtitties — Создатель субтитров"

    def __init__(self):
        super().__init__()

        # Register Windows AppUserModelID for taskbar logo
        if os.name == "nt":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("subtitties.editor.app.1")
            except Exception:
                pass

        # Set window icon from logo.ico
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "logo.ico"))
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Register all bundled custom fonts into Windows GDI for Tkinter
        register_app_fonts()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(t("app_title"))
        self.geometry("1280x860")
        self.minsize(1080, 720)

        self.configure(fg_color="#0e1017")

        self._project = SubtitleProject()
        self._current_seg_idx = -1

        self._build_toolbar()
        self._build_main()
        self._build_status_bar()

        default_style = get_preset("⚡ Unbounded Neon (Cyberpunk)")
        self._project.style = default_style
        self._style_panel.set_style(default_style)

    # ── Toolbar ──────────────────────────────────────────────────

    def _build_toolbar(self) -> None:
        tb = ctk.CTkFrame(self, height=54, corner_radius=0, fg_color="#161825", border_width=1, border_color="#24273d")
        tb.pack(fill="x")
        tb.pack_propagate(False)

        # Brand badge
        brand_frame = ctk.CTkFrame(tb, fg_color="#1f2238", corner_radius=10, height=36)
        brand_frame.pack(side="left", padx=(12, 10), pady=9)
        brand_lbl = ctk.CTkLabel(
            brand_frame, text="🎬 Subtitties", font=("Segoe UI", 13, "bold"), text_color="#A5B4FC"
        )
        brand_lbl.pack(padx=10, pady=4)

        self._open_video_btn = ctk.CTkButton(
            tb, image=get_icon("folder", size=(18, 18)), text=f" {t('load_video_btn')}", compound="left",
            width=120, height=36, corner_radius=10,
            fg_color="#22253b", hover_color="#2c304d", font=("Segoe UI", 12),
            command=self._open_video,
        )
        self._open_video_btn.pack(side="left", padx=3, pady=9)

        self._recognize_btn = ctk.CTkButton(
            tb, image=get_icon("mic", size=(18, 18)), text=f" {t('transcribe_btn').split()[0]} AI", compound="left",
            width=135, height=36, corner_radius=10,
            fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 12, "bold"),
            command=self._recognize,
        )
        self._recognize_btn.pack(side="left", padx=3, pady=9)

        self._srt_btn = ctk.CTkButton(
            tb, image=get_icon("file_text", size=(18, 18)), text=" SRT", compound="left",
            width=90, height=36, corner_radius=10,
            fg_color="#22253b", hover_color="#2c304d", font=("Segoe UI", 12),
            command=self._import_srt,
        )
        self._srt_btn.pack(side="left", padx=3, pady=9)

        self._export_btn = ctk.CTkButton(
            tb, image=get_icon("export", size=(18, 18)), text=f" {t('export_btn')}", compound="left",
            width=125, height=36, corner_radius=10,
            fg_color="#6366F1", hover_color="#4F46E5", font=("Segoe UI", 12, "bold"),
            command=self._export,
        )
        self._export_btn.pack(side="left", padx=3, pady=9)

        # Settings button
        ctk.CTkButton(
            tb, image=get_icon("settings", size=(18, 18)), text=f" {t('settings_title')}", compound="left",
            width=115, height=36, corner_radius=10,
            fg_color="#22253b", hover_color="#2c304d", font=("Segoe UI", 12),
            command=self._open_settings,
        ).pack(side="right", padx=(3, 12), pady=9)

        # Save / Load project on right side
        ctk.CTkButton(
            tb, image=get_icon("save", size=(18, 18)), text=" Project", compound="left",
            width=100, height=36, corner_radius=10,
            fg_color="#22253b", hover_color="#2c304d", font=("Segoe UI", 12),
            command=self._save_project,
        ).pack(side="right", padx=3, pady=9)

        ctk.CTkButton(
            tb, image=get_icon("folder_open", size=(18, 18)), text=" Open", compound="left",
            width=95, height=36, corner_radius=10,
            fg_color="#22253b", hover_color="#2c304d", font=("Segoe UI", 12),
            command=self._load_project,
        ).pack(side="right", padx=3, pady=9)

    def _open_settings(self) -> None:
        SettingsDialog(self, on_language_changed=self._on_language_changed)

    def _on_language_changed(self, lang_code: str) -> None:
        self.title(t("app_title"))
        self._open_video_btn.configure(text=f" {t('load_video_btn')}")
        self._export_btn.configure(text=f" {t('export_btn')}")
        self._status.configure(text=t("language_changed_note"))

    # ── Main layout ──────────────────────────────────────────────

    def _build_main(self) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=8, pady=6)

        left = ctk.CTkFrame(main, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 6), pady=0)

        self._player = VideoPlayer(
            left,
            on_time_change=self._on_time_change,
            on_position_change=self._on_position_change,
            on_rotate=self._on_video_rotate,
        )
        self._player.pack(fill="x")

        self._editor = SubtitleEditor(
            left,
            on_select=self._on_segment_select,
            on_change=self._on_segments_change,
        )
        self._editor.pack(fill="both", expand=True, pady=(6, 0))

        self._style_panel = StylePanel(
            main,
            on_style_change=self._on_style_change,
            on_grid_toggle=self._on_grid_toggle,
            on_snap_toggle=self._on_snap_toggle,
            width=380,
        )
        self._style_panel.pack(side="right", fill="y", padx=0, pady=0)

    # ── Status bar ───────────────────────────────────────────────

    def _build_status_bar(self) -> None:
        sb = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color="#12131f", border_width=1, border_color="#1e2034")
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)

        cuda_ok, gpu_name = get_cuda_info()
        gpu_status = f" | 🚀 {gpu_name}" if cuda_ok else " | 💻 CPU mode"

        self._status = ctk.CTkLabel(
            sb, text=f"Готово. Откройте видео для начала работы.{gpu_status}",
            font=("Segoe UI", 11), text_color="#888899",
        )
        self._status.pack(side="left", padx=12)

    def _set_status(self, text: str) -> None:
        self._status.configure(text=text)

    # ══════════════════════════════════════════════════════════════
    #  Actions
    # ══════════════════════════════════════════════════════════════

    def _open_video(self) -> None:
        path = filedialog.askopenfilename(
            title="Открыть видео",
            filetypes=[
                ("Видео файлы", "*.mp4 *.avi *.mkv *.mov *.webm *.wmv *.flv"),
                ("Все файлы", "*.*"),
            ],
        )
        if not path:
            return
        try:
            info = self._player.load_video(path)
            self._project.video_path = path
            self._project.video_width = info["width"]
            self._project.video_height = info["height"]
            self._project.fps = info["fps"]
            self._project.duration = info["duration"]
            self._set_status(
                f"Видео: {os.path.basename(path)} | "
                f"{info['width']}×{info['height']} | "
                f"{info['fps']:.1f} fps | "
                f"{info['duration']:.1f}с"
            )
            self._update_preview()
        except Exception as e:
            messagebox.showerror("Ошибка открытия видео", str(e))

    def _recognize(self) -> None:
        if not self._project.video_path:
            messagebox.showwarning("Внимание", "Сначала откройте видео!")
            return
        if not whisper_available():
            messagebox.showwarning(
                "faster-whisper не установлен",
                "Для распознавания речи нужен faster-whisper.\n\n"
                "Выполните: pip install faster-whisper",
            )
            return
        RecognizeDialog(
            self,
            self._project.video_path,
            on_done=self._on_recognize_done,
        )

    def _on_recognize_done(self, segments: list[SubtitleSegment]) -> None:
        self._project.segments = segments
        self._editor.set_segments(segments)
        self._player.set_segments(segments)
        self._set_status(f"✅ Распознано {len(segments)} субтитров!")
        self._update_preview()

    def _import_srt(self) -> None:
        path = filedialog.askopenfilename(
            title="Импорт SRT",
            filetypes=[("SRT файлы", "*.srt"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            segments = self._parse_srt(path)
            self._project.segments = segments
            self._editor.set_segments(segments)
            self._player.set_segments(segments)
            self._set_status(f"Импортировано {len(segments)} субтитров из SRT")
            self._update_preview()
        except Exception as e:
            messagebox.showerror("Ошибка импорта", str(e))

    def _export(self) -> None:
        if not self._project.segments:
            messagebox.showwarning("Внимание", "Нет субтитров для экспорта!")
            return
        self._project.style = self._style_panel.get_style()
        ExportDialog(self, self._project)

    def _save_project(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Сохранить проект",
            defaultextension=".subtitties",
            filetypes=[("Subtitties проект", "*.subtitties"), ("JSON", "*.json")],
        )
        if path:
            self._project.style = self._style_panel.get_style()
            self._project.segments = self._editor.get_segments()
            self._project.save(path)
            self._set_status(f"Проект сохранён: {os.path.basename(path)}")

    def _load_project(self) -> None:
        path = filedialog.askopenfilename(
            title="Загрузить проект",
            filetypes=[("Subtitties проект", "*.subtitties"), ("JSON", "*.json")],
        )
        if not path:
            return
        try:
            self._project = SubtitleProject.load(path)
            self._editor.set_segments(self._project.segments)
            self._player.set_segments(self._project.segments)
            self._style_panel.set_style(self._project.style)
            if self._project.video_path and os.path.exists(self._project.video_path):
                self._player.load_video(self._project.video_path)
            self._set_status(f"Проект загружен: {os.path.basename(path)}")
            self._update_preview()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    # ══════════════════════════════════════════════════════════════
    #  Callbacks & Synchronization
    # ══════════════════════════════════════════════════════════════

    def _on_time_change(self, t: float) -> None:
        for i, seg in enumerate(self._project.segments):
            if seg.start <= t <= seg.end:
                if i != self._current_seg_idx:
                    self._current_seg_idx = i
                    self._editor.select_segment(i)
                return
        if self._current_seg_idx != -1:
            self._current_seg_idx = -1
            self._editor.select_segment(-1)

    def _on_segment_select(self, index: int, segment: SubtitleSegment) -> None:
        self._current_seg_idx = index
        self._player.seek(segment.start)
        self._update_preview(segment.text, segment)

    def _on_segments_change(self) -> None:
        self._project.segments = self._editor.get_segments()
        self._player.set_segments(self._project.segments)
        self._update_preview()

    def _on_style_change(self, style: SubtitleStyle) -> None:
        self._project.style = style
        if style.position_x is not None:
            self._player.set_subtitle_position(style.position_x, style.position_y or 0.85)
        self._update_preview()

    def _on_position_change(self, x: float, y: float) -> None:
        self._project.style.position_x = x
        self._project.style.position_y = y
        self._style_panel.update_position_display(x, y)

    def _on_grid_toggle(self, visible: bool) -> None:
        self._player.set_grid_visible(visible)

    def _on_snap_toggle(self, enabled: bool) -> None:
        self._player.set_snap_enabled(enabled)

    def _on_video_rotate(self, w: int, h: int) -> None:
        self._project.video_width = w
        self._project.video_height = h
        self._set_status(f"🔄 Ориентация изменена: {w}×{h}")
        self._update_preview()

    # ══════════════════════════════════════════════════════════════
    #  Helpers
    # ══════════════════════════════════════════════════════════════

    def _update_preview(self, text: Optional[str] = None, segment: Optional[SubtitleSegment] = None) -> None:
        if text is None:
            t = self._player.get_current_time()
            text = ""
            for seg in self._project.segments:
                if seg.start <= t <= seg.end:
                    text = seg.text
                    segment = seg
                    break
        elif segment is None and 0 <= self._current_seg_idx < len(self._project.segments):
            segment = self._project.segments[self._current_seg_idx]

        style = self._style_panel.get_style()
        self._player.set_subtitle_preview(text, style, segment)

    @staticmethod
    def _parse_srt(path: str) -> list[SubtitleSegment]:
        with open(path, encoding="utf-8-sig") as f:
            content = f.read()

        segments: list[SubtitleSegment] = []
        blocks = content.strip().split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 2:
                continue

            time_line_idx = 1
            if "-->" not in lines[1] and len(lines) > 2 and "-->" in lines[2]:
                time_line_idx = 2

            times = lines[time_line_idx].split("-->")
            if len(times) != 2:
                continue

            start = SubtitleSegment.parse_time_srt(times[0].strip())
            end = SubtitleSegment.parse_time_srt(times[1].strip())
            text = "\n".join(lines[time_line_idx + 1:]).strip()

            if text:
                segments.append(SubtitleSegment(start=start, end=end, text=text))

        return segments
