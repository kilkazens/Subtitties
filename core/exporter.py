"""Export subtitles to SRT / ASS files and burn them into video."""

from __future__ import annotations

import os
import subprocess
import textwrap
from typing import Callable, Optional

from core.subtitle import (
    SubtitleSegment,
    SubtitleStyle,
    hex_to_ass_color,
)


# ═══════════════════════════════════════════════════════════════════
#  SRT export
# ═══════════════════════════════════════════════════════════════════

def export_srt(segments: list[SubtitleSegment], path: str) -> None:
    lines: list[str] = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(
            f"{seg.format_time_srt(seg.start)} --> {seg.format_time_srt(seg.end)}"
        )
        lines.append(seg.text.strip())
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ═══════════════════════════════════════════════════════════════════
#  ASS export
# ═══════════════════════════════════════════════════════════════════

def _build_ass_header(
    style: SubtitleStyle,
    video_width: int,
    video_height: int,
    title: str = "Subtitties Export",
) -> str:
    pc = hex_to_ass_color(style.primary_color, 0)
    sc = hex_to_ass_color(style.secondary_color, 0)
    oc = hex_to_ass_color(style.outline_color, 0)
    bc = hex_to_ass_color(style.back_color, 128)

    bold_flag = -1 if style.bold else 0
    italic_flag = -1 if style.italic else 0
    underline_flag = -1 if style.underline else 0

    border_style = 3 if style.background_box else 1

    ratio = getattr(style, "max_width_ratio", 0.80)
    margin_lr = max(10, int(video_width * (1.0 - ratio) / 2))

    header = textwrap.dedent(f"""\
    [Script Info]
    Title: {title}
    ScriptType: v4.00+
    WrapStyle: 0
    ScaledBorderAndShadow: yes
    PlayResX: {video_width}
    PlayResY: {video_height}
    YCbCr Matrix: TV.709

    [V4+ Styles]
    Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
    Style: Default,{style.font_name},{style.font_size},{pc},{sc},{oc},{bc},{bold_flag},{italic_flag},{underline_flag},0,100,100,{style.letter_spacing},0,{border_style},{style.outline_width:.1f},{style.shadow_offset:.1f},{style.alignment},{margin_lr},{margin_lr},{style.margin_v},1

    [Events]
    Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
    """)
    return header


def _build_ass_event(
    seg: SubtitleSegment,
    style: SubtitleStyle,
    video_width: int,
    video_height: int,
) -> str:
    start = seg.format_time_ass(seg.start)
    end = seg.format_time_ass(seg.end)
    text = seg.text
    if style.uppercase:
        text = text.upper()

    # Convert multiline newlines to ASS newline tag
    text = text.replace("\r\n", "\\N").replace("\n", "\\N")

    pos_tag = ""
    if style.position_x is not None and style.position_y is not None:
        px = int(style.position_x * video_width)
        py = int(style.position_y * video_height)
        pos_tag = f"{{\\pos({px},{py})}}"

    return f"Dialogue: 0,{start},{end},Default,,0,0,0,,{pos_tag}{text}"


def export_ass(
    segments: list[SubtitleSegment],
    style: SubtitleStyle,
    path: str,
    video_width: int = 1920,
    video_height: int = 1080,
) -> None:
    header = _build_ass_header(style, video_width, video_height)
    events = [
        _build_ass_event(seg, style, video_width, video_height)
        for seg in segments
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(events))
        f.write("\n")


# ═══════════════════════════════════════════════════════════════════
#  Burn subtitles into video (hardsub)
# ═══════════════════════════════════════════════════════════════════

def _get_ffmpeg() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def burn_subtitles(
    video_path: str,
    ass_path: str,
    output_path: str,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> None:
    """Burn ASS subtitles into video using ffmpeg."""
    ffmpeg = _get_ffmpeg()

    ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")
    fonts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts"))
    vf_arg = f"ass='{ass_escaped}'"
    if os.path.exists(fonts_dir):
        fonts_dir_escaped = fonts_dir.replace("\\", "/").replace(":", "\\:")
        vf_arg = f"ass='{ass_escaped}':fontsdir='{fonts_dir_escaped}'"

    cmd = [
        ffmpeg, "-y",
        "-i", video_path,
        "-vf", vf_arg,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "copy",
        "-progress", "pipe:1",
        output_path,
    ]

    if progress_callback:
        progress_callback(0.0, "Запуск FFmpeg...")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        text=True,
    )

    total_us = None
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            total_us = (frames / fps) * 1_000_000 if fps else None
            cap.release()
    except Exception:
        pass

    if proc.stdout:
        for line in proc.stdout:
            line = line.strip()
            if line.startswith("out_time_us=") and total_us:
                try:
                    current_us = int(line.split("=")[1])
                    frac = min(current_us / total_us, 1.0)
                    if progress_callback:
                        progress_callback(frac, f"Рендер... {frac * 100:.0f}%")
                except (ValueError, ZeroDivisionError):
                    pass

    proc.wait()
    if proc.returncode != 0:
        err = proc.stderr.read() if proc.stderr else ""
        raise RuntimeError(f"FFmpeg error:\n{err}")

    if progress_callback:
        progress_callback(1.0, "Экспорт завершён!")
