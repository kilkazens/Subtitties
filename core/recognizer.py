"""Speech recognition engine – uses *faster-whisper* with CUDA/CPU, DLL auto-discovery, dynamic 3-5 word chunking, and PyAV compatibility."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from typing import Callable, Optional

from core.subtitle import SubtitleSegment

# Disable HuggingFace symlinks warning on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# ── Patch PyAV 19.x compatibility (removes deprecated metadata_errors) ──
try:
    import av
    _orig_av_open = av.open
    def _safe_av_open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return _orig_av_open(*args, **kwargs)
    av.open = _safe_av_open
except Exception:
    pass

# ── Add NVIDIA CUDA DLLs to search path on Windows ───────────────
def _setup_cuda_dlls() -> bool:
    has_cublas = False
    try:
        import site
        for sp in site.getsitepackages():
            nvidia_dir = os.path.join(sp, "nvidia")
            if os.path.exists(nvidia_dir):
                for sub in os.listdir(nvidia_dir):
                    bin_dir = os.path.join(nvidia_dir, sub, "bin")
                    if os.path.exists(bin_dir):
                        if hasattr(os, "add_dll_directory"):
                            try:
                                os.add_dll_directory(bin_dir)
                            except Exception:
                                pass
                        if bin_dir not in os.environ.get("PATH", ""):
                            os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
                        if "cublas" in sub:
                            has_cublas = True
    except Exception:
        pass
    return has_cublas

_HAS_CUBLAS_DLL = _setup_cuda_dlls()

# ── Availability flag ────────────────────────────────────────────
_HAS_FASTER_WHISPER = False
try:
    from faster_whisper import WhisperModel, BatchedInferencePipeline  # type: ignore
    _HAS_FASTER_WHISPER = True
except ImportError:
    WhisperModel = None  # type: ignore
    BatchedInferencePipeline = None  # type: ignore


# ── Models ───────────────────────────────────────────────────────
MODEL_SIZES = [
    "small",
    "base",
    "tiny",
    "large-v3-turbo",
    "medium",
    "large-v3",
]

MODEL_DESCRIPTIONS = {
    "small": "📝 Small — Идеальный баланс для русского языка (~480 МБ)",
    "base": "🔄 Base — Быстрый и лёгкий (~140 МБ)",
    "tiny": "⚡ Tiny — Самый компактный (~75 МБ)",
    "large-v3-turbo": "🚀 Large-v3-Turbo — Новейший быстрый флагман от OpenAI (~1.5 ГБ)",
    "medium": "🎯 Medium — Высокая точность для сложных терминов (~1.5 ГБ)",
    "large-v3": "🏆 Large-v3 — Максимальная точность (~3 ГБ)",
}

# ── Languages ────────────────────────────────────────────────────
LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "auto": "🌐 Автоопределение",
    "en": "🇬🇧 English",
    "uk": "🇺🇦 Українська",
    "es": "🇪🇸 Español",
    "fr": "🇫🇷 Français",
    "de": "🇩🇪 Deutsch",
    "ja": "🇯🇵 日本語",
    "ko": "🇰🇷 한국어",
    "zh": "🇨🇳 中文",
    "ar": "🇸🇦 العربية",
    "pt": "🇧🇷 Português",
    "it": "🇮🇹 Italiano",
    "tr": "🇹🇷 Türkçe",
    "pl": "🇵🇱 Polski",
    "hi": "🇮🇳 हिन्दी",
    "kk": "🇰🇿 Қазақша",
}


def is_available() -> bool:
    """Check if the speech recognition engine is available."""
    return _HAS_FASTER_WHISPER


def is_model_cached(model_size: str) -> bool:
    """Check if model.bin already exists in local HuggingFace cache."""
    try:
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        if not os.path.exists(cache_dir):
            return False

        candidates = [
            f"models--Systran--faster-whisper-{model_size}",
            f"models--Systran--faster-{model_size}",
        ]
        for folder in os.listdir(cache_dir):
            if any(folder.lower() == c.lower() for c in candidates):
                snap_dir = os.path.join(cache_dir, folder, "snapshots")
                if os.path.exists(snap_dir):
                    for s in os.listdir(snap_dir):
                        bin_path = os.path.join(snap_dir, s, "model.bin")
                        if os.path.exists(bin_path) and os.path.getsize(bin_path) > 10_000_000:
                            return True
    except Exception:
        pass
    return False


def get_cuda_info() -> tuple[bool, str]:
    """Detect NVIDIA CUDA support and device name."""
    try:
        import ctranslate2
        _setup_cuda_dlls()
        if ctranslate2.get_cuda_device_count() > 0:
            gpu_name = "NVIDIA GPU"
            try:
                proc = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    gpu_name = proc.stdout.strip().split("\n")[0].strip()
            except Exception:
                pass
            return True, gpu_name
    except Exception:
        pass
    return False, ""


def get_ffmpeg_path() -> str:
    """Return path to ffmpeg binary (bundled via imageio-ffmpeg or system)."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    return "ffmpeg"


def _extract_audio(video_path: str, ffmpeg: str) -> str:
    """Extract audio from video to a temporary WAV file for Whisper."""
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    cmd = [
        ffmpeg, "-y", "-i", video_path,
        "-vn",                    # no video
        "-acodec", "pcm_s16le",   # 16-bit PCM
        "-ar", "16000",           # 16 kHz (Whisper native sample rate)
        "-ac", "1",               # mono
        tmp.name,
    ]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"FFmpeg ошибка извлечения аудио:\n{proc.stderr.decode(errors='replace')}"
        )
    return tmp.name


def _chunk_words_to_segments(words, min_words: int = 3, max_words: int = 5) -> list[SubtitleSegment]:
    """Group word timestamps into dynamic chunks of 3-5 words with word timestamps preserved."""
    chunks: list[SubtitleSegment] = []
    curr = []

    for w in words:
        curr.append(w)
        text = w.word.strip()
        ends_punc = text.endswith((".", "!", "?", ";", ":"))
        if len(curr) >= max_words or (len(curr) >= min_words and ends_punc):
            words_dict = [{"word": x.word.strip(), "start": x.start, "end": x.end} for x in curr]
            chunks.append(
                SubtitleSegment(
                    start=round(curr[0].start, 3),
                    end=round(curr[-1].end, 3),
                    text=" ".join(x.word.strip() for x in curr),
                    words=words_dict,
                )
            )
            curr = []

    if curr:
        words_dict = [{"word": x.word.strip(), "start": x.start, "end": x.end} for x in curr]
        chunks.append(
            SubtitleSegment(
                start=round(curr[0].start, 3),
                end=round(curr[-1].end, 3),
                text=" ".join(x.word.strip() for x in curr),
                words=words_dict,
            )
        )
    return chunks


class SpeechRecognizer:
    """Wraps faster-whisper with support for CUDA/CPU, auto-fallback, and PyAV compatibility."""

    def __init__(
        self,
        model_size: str = "small",
        device: str = "auto",
        compute_type: str = "auto",
        status_callback: Optional[Callable[[str], None]] = None,
    ):
        if not _HAS_FASTER_WHISPER:
            raise RuntimeError(
                "faster-whisper не установлен.\n"
                "Выполните: pip install faster-whisper"
            )

        _setup_cuda_dlls()
        cuda_ok, _ = get_cuda_info()

        if device == "auto":
            device = "cuda" if cuda_ok else "cpu"
        elif device == "cuda" and not cuda_ok:
            device = "cpu"

        if compute_type == "auto":
            compute_type = "float16" if device == "cuda" else "int8"

        self.device = device
        self.compute_type = compute_type
        self.model_size = model_size
        self._status_callback = status_callback

        is_cached = is_model_cached(model_size)
        if status_callback:
            if is_cached:
                dev_text = "видеопамять GPU" if device == "cuda" else "память CPU"
                status_callback(f"🚀 Загрузка '{model_size}' в {dev_text}...")
            else:
                status_callback(
                    f"🌐 Загрузка модели '{model_size}' из сети (только 1 раз)..."
                )

        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                local_files_only=is_cached,
            )
        except Exception as e:
            if device == "cuda":
                if status_callback:
                    status_callback("⚠️ Переключаюсь на быстрый процессор (CPU)...")
                self.device = "cpu"
                self.compute_type = "int8"
                self.model = WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8",
                    local_files_only=is_cached,
                )
            else:
                raise e

    def transcribe(
        self,
        video_path: str,
        language: Optional[str] = None,
        vad_filter: bool = True,
        dynamic_words: bool = True,
        use_batched: bool = False,
        batch_size: int = 8,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> list[SubtitleSegment]:
        """Transcribe video audio with automatic CPU fallback and dynamic 3-5 word chunking."""
        if progress_callback:
            progress_callback(0.05, "Извлечение аудиодорожки из видео...")

        ffmpeg = get_ffmpeg_path()
        audio_path = _extract_audio(video_path, ffmpeg)

        try:
            lang = language if language and language != "auto" else None
            vad_params = dict(
                min_silence_duration_ms=400,
                speech_pad_ms=200,
            ) if vad_filter else None

            try:
                return self._do_transcribe(
                    audio_path, lang, vad_filter, vad_params, dynamic_words, progress_callback
                )
            except RuntimeError as err:
                err_str = str(err).lower()
                if "cublas" in err_str or "cuda" in err_str or "cudnn" in err_str:
                    if progress_callback:
                        progress_callback(0.10, "⚡ Переключаюсь на процессор (CPU)...")
                    self.device = "cpu"
                    self.compute_type = "int8"
                    is_cached = is_model_cached(self.model_size)
                    self.model = WhisperModel(
                        self.model_size,
                        device="cpu",
                        compute_type="int8",
                        local_files_only=is_cached,
                    )
                    return self._do_transcribe(
                        audio_path, lang, vad_filter, vad_params, dynamic_words, progress_callback
                    )
                else:
                    raise err

        finally:
            try:
                os.unlink(audio_path)
            except OSError:
                pass

    def _do_transcribe(
        self,
        audio_path: str,
        lang: Optional[str],
        vad_filter: bool,
        vad_params: Optional[dict],
        dynamic_words: bool,
        progress_callback: Optional[Callable[[float, str], None]],
    ) -> list[SubtitleSegment]:
        dev_label = "GPU (CUDA)" if self.device == "cuda" else "CPU (процессор)"
        if progress_callback:
            progress_callback(0.12, f"Распознавание речи на {dev_label}...")

        segments_gen, info = self.model.transcribe(
            audio_path,
            language=lang,
            beam_size=5,
            vad_filter=vad_filter,
            vad_parameters=vad_params,
            word_timestamps=True,
        )

        total_duration = info.duration or 1.0
        detected_lang = info.language or (lang or "ru")

        results: list[SubtitleSegment] = []
        for seg in segments_gen:
            # If dynamic words requested and word timestamps available
            if dynamic_words and hasattr(seg, "words") and seg.words:
                chunks = _chunk_words_to_segments(seg.words, min_words=3, max_words=5)
                results.extend(chunks)
            else:
                text = seg.text.strip()
                if not text:
                    continue
                if dynamic_words:
                    sub_seg = SubtitleSegment(start=round(seg.start, 3), end=round(seg.end, 3), text=text)
                    results.extend(sub_seg.split_into_dynamic_chunks(3, 5))
                else:
                    results.append(SubtitleSegment(
                        start=round(seg.start, 3),
                        end=round(seg.end, 3),
                        text=text,
                    ))

            if progress_callback:
                frac = min(0.12 + 0.85 * (seg.end / total_duration), 0.98)
                progress_callback(
                    frac,
                    f"Создано {len(results)} динамичных фраз ({detected_lang}) | {seg.end:.0f}с / {total_duration:.0f}с"
                )

        if progress_callback:
            progress_callback(1.0, f"Готово! Всего создано {len(results)} динамичных субтитров.")

        return results
