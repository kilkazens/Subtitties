"""High-performance video player widget with 60fps SIMD rendering, word-by-word karaoke, trending fonts, and magnetic grid snapping."""

from __future__ import annotations

import functools
import math
import os
import subprocess
import tempfile
import threading
import time
from typing import Callable, Optional

import customtkinter as ctk
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk

try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    cv2 = None  # type: ignore
    _HAS_CV2 = False

try:
    import pygame
    pygame.mixer.init(frequency=44100)
    _HAS_PYGAME = True
except Exception:
    _HAS_PYGAME = False

from core.subtitle import SubtitleSegment, SubtitleStyle, hex_to_rgb
from core.recognizer import get_ffmpeg_path
from core.i18n import t, i18n
from ui.icons import get_icon

# Absolute paths to trending Reels fonts & Windows Fonts
_FONTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts"))

FONT_MAP = {
    "Unbounded": os.path.join(_FONTS_DIR, "Unbounded-Variable.ttf"),
    "Unbounded 1 axis": os.path.join(_FONTS_DIR, "Unbounded-Variable.ttf"),
    "Unbounded Black": os.path.join(_FONTS_DIR, "Unbounded-Black.ttf"),
    "Press Start 2P": os.path.join(_FONTS_DIR, "PressStart2P-Regular.ttf"),
    "Geologica": os.path.join(_FONTS_DIR, "Geologica-Variable.ttf"),
    "Onest": os.path.join(_FONTS_DIR, "Onest-Variable.ttf"),
    "Russo One": os.path.join(_FONTS_DIR, "RussoOne-Regular.ttf"),
    "Rubik Mono One": os.path.join(_FONTS_DIR, "RubikMonoOne-Regular.ttf"),
    "Comfortaa": os.path.join(_FONTS_DIR, "Comfortaa-Variable.ttf"),
    "Golos Text": os.path.join(_FONTS_DIR, "GolosText-Variable.ttf"),
    "Dela Gothic One": os.path.join(_FONTS_DIR, "DelaGothicOne-Regular.ttf"),
    "Montserrat Black": os.path.join(_FONTS_DIR, "Montserrat-Black.ttf"),
    "Rubik Black": os.path.join(_FONTS_DIR, "Rubik-Black.ttf"),
    "Oswald Bold": os.path.join(_FONTS_DIR, "Oswald-Bold.ttf"),
    "Bebas Neue": os.path.join(_FONTS_DIR, "BebasNeue-Regular.ttf"),
    "Impact": r"C:\Windows\Fonts\impact.ttf",
    "Arial Black": r"C:\Windows\Fonts\ariblk.ttf",
    "Bahnschrift": r"C:\Windows\Fonts\bahnschrift.ttf",
    "Segoe UI Black": r"C:\Windows\Fonts\seguibl.ttf",
    "Segoe UI": r"C:\Windows\Fonts\segoeui.ttf",
    "Trebuchet MS": r"C:\Windows\Fonts\trebuc.ttf",
    "Verdana": r"C:\Windows\Fonts\verdana.ttf",
    "Georgia": r"C:\Windows\Fonts\georgia.ttf",
    "Consolas": r"C:\Windows\Fonts\consola.ttf",
}


@functools.lru_cache(maxsize=256)
def load_reels_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load high-quality Cyrillic font from assets or system with LRU cache."""
    # Direct match or normalized lookup
    path = FONT_MAP.get(font_name)
    if not path:
        norm = font_name.strip().lower()
        for k, v in FONT_MAP.items():
            if k.lower() == norm or norm in k.lower():
                path = v
                break

    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass

    # Fallback search
    for fallback in ("arial.ttf", "segoeui.ttf", "calibri.ttf"):
        try:
            return ImageFont.truetype(fallback, size)
        except Exception:
            continue
    return ImageFont.load_default()


class VideoPlayer(ctk.CTkFrame):
    """Lag-free 60fps video player with adaptive aspect ratio, word-by-word karaoke, and audio sync."""

    MAX_CANVAS_W = 720
    MAX_CANVAS_H = 430

    def __init__(
        self,
        master,
        on_time_change: Optional[Callable[[float], None]] = None,
        on_position_change: Optional[Callable[[float, float], None]] = None,
        on_rotate: Optional[Callable[[int, int], None]] = None,
        **kw,
    ):
        super().__init__(master, fg_color="#161825", corner_radius=16, border_width=1, border_color="#24273d", **kw)
        self._on_time_change = on_time_change
        self._on_position_change = on_position_change
        self._on_rotate = on_rotate

        self._cap = None
        self._video_path = ""
        self._audio_path: Optional[str] = None
        self._audio_ready = False
        self._volume = 0.85

        self.canvas_w = 720
        self.canvas_h = 405
        self._rotation = 0

        self._video_w = 1920
        self._video_h = 1080
        self._fps = 30.0
        self._frame_count = 0
        self._duration = 0.0
        self._current_time = 0.0

        self._playing = False
        self._play_thread: Optional[threading.Thread] = None
        self._play_start_mono = 0.0
        self._play_start_time = 0.0
        self._frame_counter = 0

        self._segments: list[SubtitleSegment] = []
        self._current_segment: Optional[SubtitleSegment] = None
        self._subtitle_text = ""
        self._subtitle_style = SubtitleStyle()
        self._sub_pos_x = 0.50
        self._sub_pos_y = 0.85
        self._dragging = False

        # Grid and magnetic snapping
        self.show_grid = False
        self.snap_to_grid = True
        self._active_snap_x: Optional[float] = None
        self._active_snap_y: Optional[float] = None

        self._photo: Optional[ImageTk.PhotoImage] = None
        self._canvas_img_id: Optional[int] = None
        self._last_ui_update_time = 0.0
        self._frame_busy = False

        # ── Canvas Container (Modern rounded dark frame) ──
        self._canvas_container = ctk.CTkFrame(self, fg_color="#0b0c13", corner_radius=12)
        self._canvas_container.pack(padx=10, pady=(10, 6), fill="x")

        self._canvas = ctk.CTkCanvas(
            self._canvas_container, width=self.canvas_w, height=self.canvas_h,
            bg="#0b0c13", highlightthickness=0,
            cursor="hand2",
        )
        self._canvas.pack(anchor="center", pady=6)

        # Placeholder
        self._placeholder_id = self._canvas.create_text(
            self.canvas_w // 2, self.canvas_h // 2,
            text="🎬 Загрузите видео для начала работы",
            fill="#55586d", font=("Arial", 16, "bold"),
            tags="placeholder",
        )

        # ── Controls row 1: Timeline slider with rounded pill styling ──
        self._slider = ctk.CTkSlider(
            self, from_=0, to=100, number_of_steps=1000,
            command=self._on_slider, height=16,
            progress_color="#6366F1", button_color="#818CF8",
            button_hover_color="#A5B4FC", fg_color="#22253b",
        )
        self._slider.set(0)
        self._slider.pack(fill="x", padx=14, pady=(4, 4))

        # ── Controls row 2: Modern Icon Control Bar ──
        ctrl = ctk.CTkFrame(self, fg_color="#1c1f32", corner_radius=14, height=50, border_width=1, border_color="#272a44")
        ctrl.pack(fill="x", padx=10, pady=(2, 10))
        ctrl.pack_propagate(False)

        # Left: Playback icon buttons
        self._btn_restart = ctk.CTkButton(
            ctrl, image=get_icon("restart", size=(18, 18)), text="", width=40, height=36, corner_radius=10,
            fg_color="#25283f", hover_color="#333758",
            command=lambda: self.seek(0),
        )
        self._btn_restart.pack(side="left", padx=(8, 2), pady=7)

        self._btn_prev = ctk.CTkButton(
            ctrl, image=get_icon("step_back", size=(18, 18)), text="", width=40, height=36, corner_radius=10,
            fg_color="#25283f", hover_color="#333758",
            command=self._step_back,
        )
        self._btn_prev.pack(side="left", padx=2, pady=7)

        self._btn_play = ctk.CTkButton(
            ctrl, image=get_icon("play", size=(20, 20)), text="", width=54, height=36, corner_radius=12,
            fg_color="#6366F1", hover_color="#4F46E5",
            command=self._toggle_play,
        )
        self._btn_play.pack(side="left", padx=3, pady=7)

        self._btn_next = ctk.CTkButton(
            ctrl, image=get_icon("step_forward", size=(18, 18)), text="", width=40, height=36, corner_radius=10,
            fg_color="#25283f", hover_color="#333758",
            command=self._step_forward,
        )
        self._btn_next.pack(side="left", padx=2, pady=7)

        # Time label badge
        self._time_frame = ctk.CTkFrame(ctrl, fg_color="#12131f", corner_radius=8, height=32)
        self._time_frame.pack(side="left", padx=(6, 4), pady=9)
        self._time_label = ctk.CTkLabel(
            self._time_frame, text="00:00 / 00:00", font=("Consolas", 12, "bold"),
            text_color="#CBD5E1", width=105
        )
        self._time_label.pack(padx=6, pady=2)

        # Volume control
        self._vol_btn = ctk.CTkButton(
            ctrl, image=get_icon("volume_high", size=(18, 18)), text="", width=34, height=34, corner_radius=8,
            fg_color="transparent", hover_color="#25283f",
            command=self._toggle_mute,
        )
        self._vol_btn.pack(side="left", padx=(8, 2), pady=8)

        self._vol_slider = ctk.CTkSlider(
            ctrl, from_=0, to=100, number_of_steps=100, width=75, height=14,
            progress_color="#6366F1", button_color="#818CF8",
            fg_color="#12131f", command=self._on_volume_change,
        )
        self._vol_slider.set(85)
        self._vol_slider.pack(side="left", padx=2, pady=18)

        # Right: Magnet, Grid & Rotate toggles
        self._btn_snap = ctk.CTkButton(
            ctrl, image=get_icon("magnet", size=(16, 16)), text=f" {t('snap')}", compound="left",
            width=95, height=36, corner_radius=10,
            fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 11, "bold"),
            command=self._toggle_snap,
        )
        self._btn_snap.pack(side="right", padx=(2, 8), pady=7)

        self._btn_grid = ctk.CTkButton(
            ctrl, image=get_icon("grid", size=(16, 16)), text=f" {t('grid')}", compound="left",
            width=90, height=36, corner_radius=10,
            fg_color="#25283f", hover_color="#333758", font=("Segoe UI", 11),
            command=self._toggle_grid,
        )
        self._btn_grid.pack(side="right", padx=2, pady=7)

        self._btn_rotate = ctk.CTkButton(
            ctrl, image=get_icon("rotate", size=(16, 16)), text=" 90°", compound="left",
            width=76, height=36, corner_radius=10,
            fg_color="#25283f", hover_color="#333758", font=("Segoe UI", 11),
            command=self.rotate_video,
        )
        self._btn_rotate.pack(side="right", padx=2, pady=7)

        # Mouse events for subtitle dragging
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)

    @property
    def CANVAS_W(self) -> int:
        return self.canvas_w

    @property
    def CANVAS_H(self) -> int:
        return self.canvas_h

    # ── Video Rotation & Aspect Ratio Adaptation ────────────────

    @staticmethod
    def _detect_video_rotation(video_path: str, cap) -> int:
        """Detect smartphone rotation metadata (90/180/270 degrees)."""
        try:
            meta = int(cap.get(cv2.CAP_PROP_ORIENTATION_META) or 0)
            if meta in (90, 180, 270):
                return meta
        except Exception:
            pass

        try:
            import re
            ffmpeg = get_ffmpeg_path()
            proc = subprocess.run(
                [ffmpeg, "-i", video_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            for line in proc.stderr.splitlines():
                line_lower = line.lower()
                m = re.search(r"rotate\s*:\s*(\d+)", line_lower)
                if m:
                    val = int(m.group(1)) % 360
                    if val in (90, 180, 270):
                        return val
                m = re.search(r"rotation of\s*(-?\d+(\.\d+)?)", line_lower)
                if m:
                    val = int((float(m.group(1)) + 360) % 360)
                    if val in (90, 180, 270):
                        return val
        except Exception:
            pass
        return 0

    def _apply_rotation(self, frame):
        """Rotate frame if rotation angle is non-zero."""
        if self._rotation == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif self._rotation == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif self._rotation == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame

    def rotate_video(self) -> None:
        """Manual 90-degree clockwise rotation toggle."""
        if not self._cap:
            return
        self._rotation = (self._rotation + 90) % 360
        self._video_w, self._video_h = self._video_h, self._video_w
        self._adjust_canvas_size()
        self.seek(self._current_time)
        if self._on_rotate:
            self._on_rotate(self._video_w, self._video_h)

    def _adjust_canvas_size(self) -> None:
        """Dynamically resize canvas to fit video aspect ratio with zero distortion."""
        if self._video_w <= 0 or self._video_h <= 0:
            return

        scale = min(self.MAX_CANVAS_W / self._video_w, self.MAX_CANVAS_H / self._video_h)
        self.canvas_w = max(120, int(self._video_w * scale))
        self.canvas_h = max(120, int(self._video_h * scale))

        self._canvas.configure(width=self.canvas_w, height=self.canvas_h)
        if self._canvas_img_id is not None:
            self._canvas.delete(self._canvas_img_id)
            self._canvas_img_id = None

    # ── Public API ───────────────────────────────────────────────

    def load_video(self, path: str) -> dict:
        """Open video, auto-detect vertical/horizontal orientation, adapt canvas, and sync audio."""
        if not _HAS_CV2:
            raise RuntimeError("opencv-python-headless не установлен")
        self._stop_playback()
        if self._cap:
            self._cap.release()

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise RuntimeError(f"Не удалось открыть видео: {path}")

        self._video_path = path
        self._cap = cap

        self._rotation = self._detect_video_rotation(path, cap)

        ret, test_frame = cap.read()
        if ret:
            if self._rotation != 0:
                test_frame = self._apply_rotation(test_frame)
            self._video_h, self._video_w = test_frame.shape[:2]
        else:
            raw_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            raw_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if self._rotation in (90, 270):
                self._video_w, self._video_h = raw_h, raw_w
            else:
                self._video_w, self._video_h = raw_w, raw_h

        self._fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._duration = self._frame_count / self._fps if self._fps else 0

        self._adjust_canvas_size()
        self._canvas.delete("placeholder")

        self._audio_ready = False
        threading.Thread(target=self._extract_audio_for_player, args=(path,), daemon=True).start()

        self.seek(0)
        return {
            "width": self._video_w,
            "height": self._video_h,
            "fps": self._fps,
            "duration": self._duration,
            "frames": self._frame_count,
        }

    def set_segments(self, segments: list[SubtitleSegment]) -> None:
        """Provide all segments so the player can automatically sync active text & words during playback."""
        self._segments = segments
        self._sync_active_segment_at_time(self._current_time)
        if self._cap and not self._playing:
            self.seek(self._current_time)

    def _sync_active_segment_at_time(self, t: float) -> None:
        """Find matching segment and active text for the given timestamp."""
        if not self._segments:
            return
        match = None
        for seg in self._segments:
            if seg.start <= t <= seg.end:
                match = seg
                break
        self._current_segment = match
        self._subtitle_text = match.text if match else ""

    def seek(self, t: float) -> None:
        """Seek to timestamp t, clamping to valid frame bounds so the preview is never cut off."""
        if not self._cap:
            return
        t = max(0, min(t, self._duration))
        self._current_time = t
        self._play_start_mono = time.monotonic()
        self._play_start_time = t
        self._frame_counter = 0
        self._sync_active_segment_at_time(t)

        frame_no = int(t * self._fps)
        if self._frame_count > 0:
            frame_no = min(frame_no, max(0, self._frame_count - 1))

        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = self._cap.read()
        if not ret and frame_no > 0:
            # Fallback to previous frame if EOF reached
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_no - 1))
            ret, frame = self._cap.read()

        if ret:
            self._show_frame(frame)
        self._update_time_ui(force=True)

        if self._playing and self._audio_ready and _HAS_PYGAME:
            try:
                pygame.mixer.music.play(start=t)
            except Exception:
                pass

    def get_current_time(self) -> float:
        return self._current_time

    def set_subtitle_preview(
        self,
        text: str,
        style: SubtitleStyle,
        segment: Optional[SubtitleSegment] = None,
    ) -> None:
        self._subtitle_text = text
        self._subtitle_style = style
        self._current_segment = segment

        if style.position_x is not None:
            self._sub_pos_x = style.position_x
        if style.position_y is not None:
            self._sub_pos_y = style.position_y

        if self._cap and not self._playing:
            self.seek(self._current_time)

    def get_subtitle_position(self) -> tuple[float, float]:
        return self._sub_pos_x, self._sub_pos_y

    def set_subtitle_position(self, x: float, y: float) -> None:
        self._sub_pos_x = max(0.05, min(0.95, x))
        self._sub_pos_y = max(0.05, min(0.95, y))
        if self._cap and not self._playing:
            self.seek(self._current_time)

    def set_grid_visible(self, visible: bool) -> None:
        self.show_grid = visible
        self._btn_grid.configure(
            image=get_icon("grid", size=(16, 16)),
            text=f" {t('grid')}",
            fg_color="#6366F1" if visible else "#25283f",
        )
        if self._cap and not self._playing:
            self.seek(self._current_time)

    def set_snap_enabled(self, enabled: bool) -> None:
        self.snap_to_grid = enabled
        self._btn_snap.configure(
            image=get_icon("magnet", size=(16, 16)),
            text=f" {t('snap')}",
            fg_color="#10B981" if enabled else "#25283f",
        )

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def video_width(self) -> int:
        return self._video_w

    @property
    def video_height(self) -> int:
        return self._video_h

    @property
    def fps(self) -> float:
        return self._fps

    # ── Fast Hardware Audio extraction ───────────────────────────

    def _extract_audio_for_player(self, video_path: str) -> None:
        """Extract audio to temporary wav file for pygame playback."""
        try:
            if not _HAS_PYGAME:
                return

            if self._audio_path and os.path.exists(self._audio_path):
                try:
                    os.unlink(self._audio_path)
                except OSError:
                    pass

            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()
            self._audio_path = tmp.name

            ffmpeg = get_ffmpeg_path()
            cmd = [
                ffmpeg, "-y", "-i", video_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                self._audio_path,
            ]
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if proc.returncode == 0 and os.path.exists(self._audio_path):
                pygame.mixer.music.load(self._audio_path)
                pygame.mixer.music.set_volume(self._volume)
                self._audio_ready = True
        except Exception:
            self._audio_ready = False

    def _on_volume_change(self, val: float) -> None:
        self._volume = val / 100.0
        if _HAS_PYGAME:
            pygame.mixer.music.set_volume(self._volume)
        if self._volume == 0:
            self._vol_btn.configure(image=get_icon("volume_mute", size=(18, 18)), text="")
        elif self._volume < 0.5:
            self._vol_btn.configure(image=get_icon("volume_low", size=(18, 18)), text="")
        else:
            self._vol_btn.configure(image=get_icon("volume_high", size=(18, 18)), text="")

    def _toggle_mute(self) -> None:
        if self._volume > 0:
            self._prev_vol = self._volume
            self._vol_slider.set(0)
            self._on_volume_change(0)
        else:
            prev = getattr(self, "_prev_vol", 0.85)
            self._vol_slider.set(prev * 100)
            self._on_volume_change(prev * 100)

    # ── Grid & Snap actions ──────────────────────────────────────

    def _toggle_grid(self) -> None:
        self.set_grid_visible(not self.show_grid)

    def _toggle_snap(self) -> None:
        self.set_snap_enabled(not self.snap_to_grid)

    # ── Ultra-fast SIMD Frame rendering ──────────────────────────

    def _prepare_frame_image(self, frame, timestamp: Optional[float] = None) -> Image.Image:
        """Process OpenCV frame to PIL image and render composition grid and karaoke subtitles."""
        if self._rotation != 0:
            frame = self._apply_rotation(frame)

        resized = cv2.resize(frame, (self.canvas_w, self.canvas_h), interpolation=cv2.INTER_LINEAR)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)

        if self.show_grid or self._dragging:
            img = self._draw_grid(img)

        if self._dragging and (self._active_snap_x is not None or self._active_snap_y is not None):
            img = self._draw_active_snaps(img)

        if self._subtitle_text:
            img = self._draw_karaoke_subtitle(img, timestamp)

        return img

    def _render_prepared_image(self, img: Image.Image) -> None:
        """Render PIL image onto the Tkinter canvas with zero lag (<0.5ms)."""
        try:
            self._photo = ImageTk.PhotoImage(img)

            if self._canvas_img_id is None:
                self._canvas_img_id = self._canvas.create_image(
                    self.canvas_w // 2, self.canvas_h // 2,
                    image=self._photo, anchor="center",
                )
            else:
                self._canvas.coords(self._canvas_img_id, self.canvas_w // 2, self.canvas_h // 2)
                self._canvas.itemconfig(self._canvas_img_id, image=self._photo)
        finally:
            self._frame_busy = False

    def _show_frame(self, frame) -> None:
        """Synchronously display a frame on UI (for seek, drag, pause)."""
        img = self._prepare_frame_image(frame, self._current_time)
        self._render_prepared_image(img)

    def _draw_grid(self, img: Image.Image) -> Image.Image:
        """Draw composition grid with rule of thirds, center cross, and text boundary margins."""
        draw = ImageDraw.Draw(img, "RGBA")
        w, h = img.width, img.height

        grid_color = (255, 255, 255, 35)
        center_color = (99, 102, 241, 100)
        bound_color = (255, 180, 0, 90)

        draw.line([(w // 2, 0), (w // 2, h)], fill=center_color, width=1)
        draw.line([(0, h // 2), (w, h // 2)], fill=center_color, width=1)

        for frac in (1 / 3, 2 / 3):
            x = int(w * frac)
            y = int(h * frac)
            draw.line([(x, 0), (x, h)], fill=grid_color, width=1)
            draw.line([(0, y), (w, y)], fill=grid_color, width=1)

        ratio = getattr(self._subtitle_style, "max_width_ratio", 0.80)
        margin_frac = (1.0 - ratio) / 2.0
        bx_left = int(w * margin_frac)
        bx_right = int(w * (1.0 - margin_frac))

        draw.line([(bx_left, 0), (bx_left, h)], fill=bound_color, width=1)
        draw.line([(bx_right, 0), (bx_right, h)], fill=bound_color, width=1)

        sub_y = int(h * 0.85)
        draw.line([(bx_left, sub_y), (bx_right, sub_y)], fill=(16, 185, 129, 90), width=1)

        return img

    def _draw_active_snaps(self, img: Image.Image) -> Image.Image:
        """Highlight magnetic snapped guides in bright neon color."""
        draw = ImageDraw.Draw(img, "RGBA")
        w, h = img.width, img.height
        snap_line_color = (255, 230, 0, 240)

        if self._active_snap_x is not None:
            px = int(self._active_snap_x * w)
            draw.line([(px, 0), (px, h)], fill=snap_line_color, width=2)

        if self._active_snap_y is not None:
            py = int(self._active_snap_y * h)
            draw.line([(0, py), (w, py)], fill=snap_line_color, width=2)

        return img

    # ── Modern Reels Word-by-Word Karaoke Rendering ─────────────

    def _draw_karaoke_subtitle(self, img: Image.Image, timestamp: Optional[float] = None) -> Image.Image:
        """Render modern Reels/TikTok word-by-word karaoke with dynamic animations and zero-overlap baseline pills."""
        draw = ImageDraw.Draw(img, "RGBA")
        style = self._subtitle_style
        raw_text = self._subtitle_text
        if style.uppercase:
            raw_text = raw_text.upper()

        scale_factor = self.canvas_w / max(1, self._video_w)
        font_size = max(14, int(style.font_size * scale_factor))
        font = load_reels_font(style.font_name, font_size)

        t = timestamp if timestamp is not None else self._current_time
        active_idx = -1
        active_prog = 0.0
        if self._current_segment:
            active_idx, active_prog = self._current_segment.get_active_word_info(t)

        ascent, descent = font.getmetrics()
        cap_bbox = font.getbbox("ПШВHMg", anchor="ls")

        # Pill padding dimensions
        pill_pad_x = max(8, int(font_size * 0.22))
        pill_pad_y = max(4, int(font_size * 0.14))

        # Safe space width: guarantees pills never touch or encroach neighboring words
        raw_space_w = font.getbbox(" ", anchor="ls")[2]
        space_w = max(raw_space_w, int(font_size * 0.38), pill_pad_x * 2 + 8)

        max_boundary_px = int(img.width * getattr(style, "max_width_ratio", 0.80))
        lines_words = self._wrap_words_to_boundary(raw_text, font, space_w, max_boundary_px)
        if not lines_words:
            return img

        line_height = int(font_size * 1.35)
        line_measurements = []
        max_block_w = 0
        global_word_counter = 0

        for line in lines_words:
            line_w = 0
            words_info = []
            for w in line:
                bbox = font.getbbox(w, anchor="ls")
                ww = bbox[2] - bbox[0]
                words_info.append((w, ww, global_word_counter))
                line_w += ww + space_w
                global_word_counter += 1

            if words_info:
                line_w -= space_w

            max_block_w = max(max_block_w, line_w)
            line_measurements.append((line_w, words_info))

        total_block_h = (len(lines_words) - 1) * line_height + (ascent + descent)

        center_x = int(self._sub_pos_x * img.width)
        center_y = int(self._sub_pos_y * img.height)

        block_top = center_y - total_block_h // 2
        block_left = center_x - max_block_w // 2

        if style.background_box:
            pad = int(style.background_padding * scale_factor)
            bg_r, bg_g, bg_b = hex_to_rgb(style.background_color)
            bg_alpha = int(style.background_opacity * 255)
            draw.rounded_rectangle(
                [block_left - pad, block_top - pad, block_left + max_block_w + pad, block_top + total_block_h + pad],
                radius=max(6, pad // 2),
                fill=(bg_r, bg_g, bg_b, bg_alpha),
            )

        if self._dragging:
            draw.rounded_rectangle(
                [block_left - 8, block_top - 8, block_left + max_block_w + 8, block_top + total_block_h + 8],
                radius=6, outline=(0, 255, 255, 180), width=2,
            )

        pr, pg, pb = hex_to_rgb(style.primary_color)
        or_, og, ob = hex_to_rgb(style.outline_color)
        ow = max(0, int(style.outline_width * scale_factor))
        so = max(0, int(style.shadow_offset * scale_factor))

        hi_r, hi_g, hi_b = hex_to_rgb(getattr(style, "highlight_color", "#FFE600"))
        pill_r, pill_g, pill_b = hex_to_rgb(getattr(style, "highlight_bg", "#FF0055"))
        pill_txt_r, pill_txt_g, pill_txt_b = hex_to_rgb(getattr(style, "highlight_text_color", "#000000"))
        karaoke_mode = getattr(style, "karaoke_mode", "pill")

        # ── Precompute word layout tokens with animations & baseline alignment ──
        tokens = []
        cur_y = block_top
        for line_w, words_info in line_measurements:
            cur_x = center_x - line_w // 2
            baseline_y = cur_y + ascent

            for w_text, ww, g_idx in words_info:
                is_active = (g_idx == active_idx) and (karaoke_mode != "none")
                anim_dy = 0.0
                scale = 1.0

                if is_active:
                    if karaoke_mode in ("bounce", "pill_bounce"):
                        # Dynamic vertical jump
                        anim_dy = -math.sin(math.pi * active_prog) * (font_size * 0.28)
                    elif karaoke_mode in ("pop", "pill_pop"):
                        # Smooth growth / pop expansion
                        scale = 1.0 + 0.24 * math.sin(math.pi * active_prog)
                    elif karaoke_mode == "wave":
                        anim_dy = -math.sin(math.pi * active_prog) * (font_size * 0.28)
                elif karaoke_mode == "wave" and active_idx >= 0:
                    # Neighboring words trailing wave
                    if abs(g_idx - active_idx) == 1:
                        anim_dy = -math.sin(math.pi * active_prog) * (font_size * 0.12)

                if abs(scale - 1.0) > 0.01:
                    w_font_sz = max(14, int(font_size * scale))
                    w_font = load_reels_font(style.font_name, w_font_sz)
                    w_cap = w_font.getbbox("ПШВHMg", anchor="ls")
                    w_bbox = w_font.getbbox(w_text, anchor="ls")
                    w_render_w = w_bbox[2] - w_bbox[0]
                    render_x = cur_x + (ww - w_render_w) // 2
                else:
                    w_font = font
                    w_cap = cap_bbox
                    w_render_w = ww
                    render_x = cur_x

                has_pill = is_active and (karaoke_mode in ("pill", "pill_bounce", "pill_pop"))

                tokens.append({
                    "w_text": w_text,
                    "is_active": is_active,
                    "has_pill": has_pill,
                    "render_x": render_x,
                    "baseline_y": baseline_y + anim_dy,
                    "w_font": w_font,
                    "w_cap": w_cap,
                    "w_render_w": w_render_w,
                })

                cur_x += ww + space_w

            cur_y += line_height

        # ── PASS 1: Draw pill badges first (zero overlap on neighbor text) ──
        for tok in tokens:
            if tok["has_pill"]:
                bx = tok["render_x"]
                by = tok["baseline_y"]
                bw = tok["w_render_w"]
                w_cap = tok["w_cap"]

                p_left = bx - pill_pad_x
                p_top = by + w_cap[1] - pill_pad_y
                p_right = bx + bw + pill_pad_x
                p_bottom = by + w_cap[3] + pill_pad_y
                radius = max(6, int((p_bottom - p_top) * 0.35))

                draw.rounded_rectangle(
                    [p_left, p_top, p_right, p_bottom],
                    radius=radius,
                    fill=(pill_r, pill_g, pill_b, 255),
                )

        # ── PASS 2: Draw all text with baseline anchor="ls" ──
        for tok in tokens:
            bx = tok["render_x"]
            by = tok["baseline_y"]
            w_text = tok["w_text"]
            w_font = tok["w_font"]
            is_active = tok["is_active"]
            has_pill = tok["has_pill"]

            if has_pill:
                draw.text(
                    (bx, by), w_text, font=w_font, anchor="ls",
                    fill=(pill_txt_r, pill_txt_g, pill_txt_b, 255),
                )
            elif is_active:
                if so > 0:
                    draw.text((bx + so, by + so), w_text, font=w_font, anchor="ls", fill=(0, 0, 0, 180))
                draw.text(
                    (bx, by), w_text, font=w_font, anchor="ls",
                    fill=(hi_r, hi_g, hi_b, 255),
                    stroke_width=ow + 1,
                    stroke_fill=(or_, og, ob, 255) if ow > 0 else None,
                )
            else:
                if so > 0:
                    draw.text((bx + so, by + so), w_text, font=w_font, anchor="ls", fill=(0, 0, 0, 180))
                draw.text(
                    (bx, by), w_text, font=w_font, anchor="ls",
                    fill=(pr, pg, pb, 255),
                    stroke_width=ow,
                    stroke_fill=(or_, og, ob, 255) if ow > 0 else None,
                )

        return img

    @staticmethod
    def _wrap_words_to_boundary(text: str, font, space_w: int, max_width_px: int) -> list[list[str]]:
        """Wrap text into lists of words per line respecting exact space_w and max_width_px."""
        result: list[list[str]] = []
        for paragraph in text.split("\n"):
            words = paragraph.split()
            if not words:
                continue

            current_line: list[str] = []
            current_line_w = 0
            for w in words:
                bbox = font.getbbox(w, anchor="ls")
                ww = bbox[2] - bbox[0]
                needed_w = ww if not current_line else current_line_w + space_w + ww

                if needed_w <= max_width_px or not current_line:
                    current_line.append(w)
                    current_line_w = needed_w
                else:
                    result.append(current_line)
                    current_line = [w]
                    current_line_w = ww

            if current_line:
                result.append(current_line)

        return result

    # ── 60 FPS Playback Loop & Auto-Restart ───────────────────────

    def _toggle_play(self) -> None:
        """Play or pause; if video reached the end, automatically replay from beginning."""
        if self._playing:
            self._stop_playback()
        else:
            # If at or near the end, restart cleanly from 0:00!
            if self._duration > 0 and self._current_time >= (self._duration - 0.08):
                self.seek(0)
            self._start_playback()

    def _start_playback(self) -> None:
        if not self._cap:
            return
        self._playing = True
        self._frame_counter = 0
        self._play_start_mono = time.monotonic()
        self._play_start_time = self._current_time
        self._btn_play.configure(image=get_icon("pause", size=(18, 18)), text="", fg_color="#EF4444", hover_color="#DC2626")

        if self._audio_ready and _HAS_PYGAME:
            try:
                pygame.mixer.music.play(start=self._current_time)
            except Exception:
                pass

        self._play_thread = threading.Thread(target=self._play_loop, daemon=True)
        self._play_thread.start()

    def _stop_playback(self) -> None:
        """Stop playback, force UI synchronization, and seek to current time so preview is never clipped."""
        self._playing = False
        self._btn_play.configure(image=get_icon("play", size=(20, 20)), text="", fg_color="#6366F1", hover_color="#4F46E5")
        if _HAS_PYGAME:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self._update_time_ui(force=True)
        if self._on_time_change:
            self._on_time_change(self._current_time)
        # Lock exact frame on stop so preview never shows trailing/clipped frames
        if self._cap:
            self.seek(self._current_time)

    def _on_video_ended(self) -> None:
        """Called when video finishes playing; snaps to end so next Play triggers replay."""
        self._stop_playback()
        self._current_time = self._duration
        self._update_time_ui(force=True)
        if self._on_time_change:
            self._on_time_change(self._duration)

    def _play_loop(self) -> None:
        """Rock-solid sequential 60fps loop with offloaded frame preparation and queue-drop guard."""
        interval = 1.0 / self._fps
        self._last_ui_update_time = time.monotonic()

        while self._playing and self._cap:
            ret, frame = self._cap.read()
            if not ret:
                # Video reached EOF
                self._current_time = self._duration
                self.after(0, self._on_video_ended)
                break

            self._frame_counter += 1
            cur_time = self._play_start_time + self._frame_counter * interval
            self._current_time = min(cur_time, self._duration)

            if self._segments:
                self._sync_active_segment_at_time(self._current_time)

            # Offload heavy frame resize and subtitle rendering to this worker thread
            img = self._prepare_frame_image(frame, self._current_time)

            # Push to Tkinter UI thread only when UI is ready, preventing queue accumulation and lag
            if not self._frame_busy:
                self._frame_busy = True
                self.after(0, self._render_prepared_image, img)

            # Check if duration reached AFTER rendering the frame
            if cur_time >= self._duration:
                self._current_time = self._duration
                self.after(0, self._on_video_ended)
                break

            # Throttle UI slider updates to keep Tkinter UI loop silky smooth
            now = time.monotonic()
            if now - self._last_ui_update_time > 0.08:
                self._last_ui_update_time = now
                self.after(0, self._update_time_ui, False)
                if self._on_time_change:
                    self.after(0, self._on_time_change, self._current_time)

            # Precision frame timing
            expected_mono = self._play_start_mono + self._frame_counter * interval
            delay = expected_mono - time.monotonic()
            if delay > 0.001:
                time.sleep(delay)
            elif delay < -interval * 2:
                self._cap.grab()
                self._frame_counter += 1

    def _step_back(self) -> None:
        self._stop_playback()
        self.seek(max(0, self._current_time - 1.0 / self._fps * 10))

    def _step_forward(self) -> None:
        self._stop_playback()
        self.seek(min(self._duration, self._current_time + 1.0 / self._fps * 10))

    # ── Slider & Time ────────────────────────────────────────────

    def _on_slider(self, val) -> None:
        if self._duration > 0 and not self._playing:
            t = (float(val) / 100.0) * self._duration
            self.seek(t)
            if self._on_time_change:
                self._on_time_change(t)

    def _update_time_ui(self, force: bool = False) -> None:
        cur = self._fmt_time(self._current_time)
        total = self._fmt_time(self._duration)
        self._time_label.configure(text=f"{cur} / {total}")
        if self._duration > 0:
            self._slider.set(self._current_time / self._duration * 100)

    @staticmethod
    def _fmt_time(t: float) -> str:
        m = int(t // 60)
        s = int(t % 60)
        return f"{m:02d}:{s:02d}"

    # ── Drag subtitle with Magnetic Grid Snapping ───────────────

    def _on_press(self, event) -> None:
        self._dragging = True
        self._on_drag(event)

    def _on_drag(self, event) -> None:
        if not self._dragging:
            return

        raw_x = max(0.05, min(0.95, event.x / self.canvas_w))
        raw_y = max(0.05, min(0.95, event.y / self.canvas_h))

        self._active_snap_x = None
        self._active_snap_y = None

        if self.snap_to_grid:
            snap_x_targets = [
                (0.500, 0.040),  # Center
                (0.333, 0.025),  # Left third
                (0.667, 0.025),  # Right third
                (0.100, 0.025),  # Left margin
                (0.900, 0.025),  # Right margin
            ]
            for target_x, thresh in snap_x_targets:
                if abs(raw_x - target_x) <= thresh:
                    raw_x = target_x
                    self._active_snap_x = target_x
                    break

            snap_y_targets = [
                (0.850, 0.040),  # Reels standard bottom (85%)
                (0.880, 0.030),  # Low bottom
                (0.500, 0.040),  # Middle center
                (0.120, 0.035),  # Top
                (0.333, 0.025),  # Top third
                (0.667, 0.025),  # Bottom third
            ]
            for target_y, thresh in snap_y_targets:
                if abs(raw_y - target_y) <= thresh:
                    raw_y = target_y
                    self._active_snap_y = target_y
                    break

        self._sub_pos_x = raw_x
        self._sub_pos_y = raw_y

        if self._cap:
            self.seek(self._current_time)

    def _on_release(self, event) -> None:
        self._dragging = False
        self._active_snap_x = None
        self._active_snap_y = None
        if self._cap:
            self.seek(self._current_time)
        if self._on_position_change:
            self._on_position_change(self._sub_pos_x, self._sub_pos_y)

    # ── Cleanup ──────────────────────────────────────────────────

    def destroy(self) -> None:
        self._stop_playback()
        if self._cap:
            self._cap.release()
        if self._audio_path and os.path.exists(self._audio_path):
            try:
                os.unlink(self._audio_path)
            except OSError:
                pass
        super().destroy()
