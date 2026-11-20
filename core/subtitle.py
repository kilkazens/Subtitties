"""Data models for subtitles, styles, karaoke highlights, and projects."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class SubtitleStyle:
    """Describes visual typography, boundaries, and karaoke animation style."""

    font_name: str = "Montserrat Black"
    font_size: int = 56
    primary_color: str = "#FFFFFF"
    secondary_color: str = "#FFFF00"
    outline_color: str = "#000000"
    back_color: str = "#000000"
    bold: bool = True
    italic: bool = False
    underline: bool = False
    outline_width: float = 3.5
    shadow_offset: float = 1.0

    # Alignment numpad: 1-3 bottom, 4-6 middle, 7-9 top
    alignment: int = 2
    margin_v: int = 30
    margin_l: int = 20
    margin_r: int = 20

    # Custom drag position (0.0–1.0 fraction of video)
    position_x: Optional[float] = 0.50
    position_y: Optional[float] = 0.85

    # Boundary max width ratio (0.40–0.95 fraction of video width)
    max_width_ratio: float = 0.80

    # Background box behind full text
    background_box: bool = False
    background_color: str = "#000000"
    background_opacity: float = 0.70
    background_padding: int = 12

    # Uppercase transform
    uppercase: bool = True
    letter_spacing: int = 0

    # ── Karaoke / Reels animation settings ──
    karaoke_mode: str = "pill"  # "pill", "bounce", "pop", "pill_bounce", "pill_pop", "wave", "color", "none"
    highlight_color: str = "#FFE600"  # Bright yellow for active word
    highlight_bg: str = "#FF0044"  # Punchy red/pink pill background
    highlight_text_color: str = "#000000"  # Text color inside pill

    def copy(self) -> SubtitleStyle:
        return copy.deepcopy(self)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> SubtitleStyle:
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class SubtitleSegment:
    """A subtitle segment with timing, text, and optional word-level timestamps."""

    start: float  # seconds
    end: float  # seconds
    text: str = ""
    words: list[dict] = field(default_factory=list)  # [{'word': str, 'start': float, 'end': float}]

    def duration(self) -> float:
        return max(0.01, self.end - self.start)

    def get_active_word_info(self, current_time: float) -> tuple[int, float]:
        """Return (active_word_index, progress_in_word_0_to_1) for smooth dynamic animations."""
        if self.words:
            for i, w in enumerate(self.words):
                w_start = w.get("start", self.start)
                w_end = w.get("end", self.end)
                if w_start <= current_time <= w_end:
                    dur = max(0.01, w_end - w_start)
                    prog = max(0.0, min(1.0, (current_time - w_start) / dur))
                    return i, prog
            if current_time >= self.words[-1].get("end", self.end):
                return len(self.words) - 1, 1.0
            if current_time <= self.words[0].get("start", self.start):
                return 0, 0.0

        word_list = self.text.strip().split()
        if not word_list:
            return -1, 0.0

        dur = self.duration()
        t_rel = max(0.0, min(dur, current_time - self.start))
        total_words = len(word_list)
        word_dur = dur / total_words
        idx = min(int(t_rel / word_dur), total_words - 1)
        prog = (t_rel - idx * word_dur) / max(0.001, word_dur)
        return idx, max(0.0, min(1.0, prog))

    def get_active_word_index(self, current_time: float) -> int:
        """Return index of currently spoken word for karaoke highlighting."""
        return self.get_active_word_info(current_time)[0]

    def split_into_dynamic_chunks(
        self, min_words: int = 3, max_words: int = 5
    ) -> list[SubtitleSegment]:
        """Split a long segment into 3-5 word dynamic chunks with exact or interpolated word timing."""
        if self.words and len(self.words) > max_words:
            results: list[SubtitleSegment] = []
            i = 0
            while i < len(self.words):
                rem = len(self.words) - i
                take = min(max_words, rem)
                if rem <= 2 and results:
                    prev = results.pop()
                    combined_words = prev.words + self.words[i:]
                    results.append(
                        SubtitleSegment(
                            start=prev.start,
                            end=self.end,
                            text=" ".join(w["word"].strip() for w in combined_words),
                            words=combined_words,
                        )
                    )
                    break
                chunk_words = self.words[i : i + take]
                c_start = chunk_words[0]["start"]
                c_end = chunk_words[-1]["end"]
                results.append(
                    SubtitleSegment(
                        start=round(c_start, 3),
                        end=round(c_end, 3),
                        text=" ".join(w["word"].strip() for w in chunk_words),
                        words=chunk_words,
                    )
                )
                i += take
            return results

        # Fallback without word timestamps
        words = self.text.strip().split()
        if len(words) <= max_words:
            return [SubtitleSegment(start=self.start, end=self.end, text=self.text.strip(), words=self.words)]

        dur_per_word = self.duration() / len(words)
        results: list[SubtitleSegment] = []
        i = 0

        while i < len(words):
            rem = len(words) - i
            take = min(max_words, rem)
            if rem <= 2 and results:
                prev = results.pop()
                combined = prev.text + " " + " ".join(words[i:])
                results.append(SubtitleSegment(start=prev.start, end=self.end, text=combined))
                break

            chunk_words = words[i : i + take]
            chunk_start = round(self.start + i * dur_per_word, 3)
            chunk_end = (
                self.end
                if (i + take) >= len(words)
                else round(self.start + (i + take) * dur_per_word, 3)
            )

            # Generate synthetic word timestamps
            synth_words = []
            for j, cw in enumerate(chunk_words):
                w_st = round(chunk_start + j * dur_per_word, 3)
                w_en = round(chunk_start + (j + 1) * dur_per_word, 3)
                synth_words.append({"word": cw, "start": w_st, "end": w_en})

            results.append(
                SubtitleSegment(
                    start=chunk_start,
                    end=chunk_end,
                    text=" ".join(chunk_words),
                    words=synth_words,
                )
            )
            i += take

        return results

    # ── SRT helpers ──────────────────────────────────────────────
    @staticmethod
    def format_time_srt(t: float) -> str:
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int(round((t % 1) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    # ── ASS helpers ──────────────────────────────────────────────
    @staticmethod
    def format_time_ass(t: float) -> str:
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        cs = int(round((t % 1) * 100))
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "text": self.text, "words": self.words}

    @classmethod
    def from_dict(cls, data: dict) -> SubtitleSegment:
        return cls(
            start=data["start"],
            end=data["end"],
            text=data.get("text", ""),
            words=data.get("words", []),
        )


@dataclass
class SubtitleProject:
    """Full project state: video + segments + style."""

    video_path: str = ""
    segments: list[SubtitleSegment] = field(default_factory=list)
    style: SubtitleStyle = field(default_factory=SubtitleStyle)
    video_width: int = 1920
    video_height: int = 1080
    fps: float = 30.0
    duration: float = 0.0

    def save(self, path: str) -> None:
        data = {
            "video_path": self.video_path,
            "segments": [s.to_dict() for s in self.segments],
            "style": self.style.to_dict(),
            "video_width": self.video_width,
            "video_height": self.video_height,
            "fps": self.fps,
            "duration": self.duration,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> SubtitleProject:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        proj = cls()
        proj.video_path = data.get("video_path", "")
        proj.segments = [SubtitleSegment.from_dict(s) for s in data.get("segments", [])]
        proj.style = SubtitleStyle.from_dict(data.get("style", {}))
        proj.video_width = data.get("video_width", 1920)
        proj.video_height = data.get("video_height", 1080)
        proj.fps = data.get("fps", 30.0)
        proj.duration = data.get("duration", 0.0)
        return proj


# ── Colour helpers ───────────────────────────────────────────────

def hex_to_ass_color(hex_color: str, alpha: int = 0) -> str:
    """Convert '#RRGGBB' → '&HAABBGGRR' (ASS uses BGR order)."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 8:
        r, g, b, a = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16), int(hex_color[6:8], 16)
    else:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        a = alpha
    return f"&H{a:02X}{b:02X}{g:02X}{r:02X}"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"
