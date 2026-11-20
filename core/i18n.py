"""Internationalization (i18n) module for Subtitties.
Supports English (default) and Russian, with persistent user preferences.
"""

from __future__ import annotations

import json
import os
from typing import Any

_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "config.json")
)

# Supported language codes
LANG_EN = "en"
LANG_RU = "ru"

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── App & Navigation ──
    "app_title": {
        "en": "Subtitties - Modern AI Subtitles & Reels Editor",
        "ru": "Subtitties - Трендовый видеоредактор субтитров Reels/Shorts",
    },
    "settings_title": {
        "en": "Settings",
        "ru": "Настройки",
    },
    "language": {
        "en": "Language",
        "ru": "Язык",
    },
    "language_changed_note": {
        "en": "Language changed! Some changes take full effect after restart.",
        "ru": "Язык изменён! Некоторые изменения вступят в силу после перезапуска.",
    },
    "load_video_btn": {
        "en": "Open Video",
        "ru": "Открыть видео",
    },
    "export_btn": {
        "en": "Export Video",
        "ru": "Экспорт видео",
    },
    "video_not_loaded": {
        "en": "No video loaded. Open a video to start editing.",
        "ru": "Видео не загружено. Откройте видео для начала работы.",
    },

    # ── Playback & Canvas ──
    "play": {
        "en": "Play",
        "ru": "Воспроизведение",
    },
    "pause": {
        "en": "Pause",
        "ru": "Пауза",
    },
    "restart": {
        "en": "Restart",
        "ru": "С начала",
    },
    "step_back": {
        "en": "Step Back (-10 frames)",
        "ru": "Назад (-10 кадров)",
    },
    "step_forward": {
        "en": "Step Forward (+10 frames)",
        "ru": "Вперёд (+10 кадров)",
    },
    "grid": {
        "en": "Grid",
        "ru": "Сетка",
    },
    "snap": {
        "en": "Snap",
        "ru": "Магнит",
    },
    "rotate": {
        "en": "Rotate",
        "ru": "Поворот",
    },
    "drag_subtitles_hint": {
        "en": "Drag subtitles with mouse on video to position them anywhere",
        "ru": "Перетаскивайте субтитры мышкой по видео в любую точку",
    },

    # ── Transcriber / AI ──
    "transcription_title": {
        "en": "🎙️ AI Speech-to-Text (faster-whisper):",
        "ru": "🎙️ Распознавание речи (faster-whisper):",
    },
    "whisper_model": {
        "en": "Model:",
        "ru": "Модель Whisper:",
    },
    "audio_language": {
        "en": "Language:",
        "ru": "Язык речи:",
    },
    "transcribe_btn": {
        "en": "Generate Subtitles with AI",
        "ru": "Распознать речь и создать субтитры",
    },
    "transcribing_status": {
        "en": "Extracting audio and transcribing...",
        "ru": "Извлечение аудио и распознавание...",
    },
    "transcription_done": {
        "en": "Subtitles generated successfully! ({count} segments)",
        "ru": "Субтитры успешно созданы! ({count} сегментов)",
    },
    "transcription_failed": {
        "en": "Transcription failed: {error}",
        "ru": "Ошибка распознавания: {error}",
    },

    # ── Subtitle Editor Table ──
    "editor_title": {
        "en": "📝 Subtitle Segments",
        "ru": "📝 Сегменты субтитров",
    },
    "split_chunks_btn": {
        "en": "Dynamic Chunks (3-5 words)",
        "ru": "Разбить на фразы (3-5 слов)",
    },
    "add_segment_btn": {
        "en": "Add Segment",
        "ru": "Добавить фразу",
    },
    "import_srt_btn": {
        "en": "Import SRT",
        "ru": "Импорт SRT",
    },
    "export_srt_btn": {
        "en": "Export SRT",
        "ru": "Экспорт SRT",
    },
    "col_start": {
        "en": "Start",
        "ru": "Начало",
    },
    "col_end": {
        "en": "End",
        "ru": "Конец",
    },
    "col_text": {
        "en": "Subtitle Text",
        "ru": "Текст субтитров",
    },
    "col_actions": {
        "en": "Actions",
        "ru": "Действия",
    },
    "delete_segment": {
        "en": "Delete",
        "ru": "Удалить",
    },

    # ── Style Panel ──
    "style_panel_title": {
        "en": "🎨 Subtitle Design & Reels Styles",
        "ru": "🎨 Стили и оформление субтитров",
    },
    "presets_label": {
        "en": "✨ Trending Reels Presets:",
        "ru": "✨ Трендовые пресеты Reels/Shorts:",
    },
    "save_preset_btn": {
        "en": "Save Preset",
        "ru": "Сохранить пресет",
    },
    "delete_preset_btn": {
        "en": "Delete",
        "ru": "Удалить",
    },
    "save_preset_dialog_title": {
        "en": "Save Custom Preset",
        "ru": "Сохранение пресета",
    },
    "save_preset_dialog_prompt": {
        "en": "Enter a name for your custom preset:",
        "ru": "Введите название для вашего пресета:",
    },
    "preset_saved_toast": {
        "en": "Preset '{name}' saved successfully!",
        "ru": "Пресет '{name}' успешно сохранён!",
    },
    "preset_deleted_toast": {
        "en": "Preset '{name}' deleted.",
        "ru": "Пресет '{name}' удалён.",
    },

    # ── Fonts & Typography ──
    "font_family_label": {
        "en": "Font Family (Cyrillic + English):",
        "ru": "Шрифт (Кириллица + Латиница):",
    },
    "import_font_btn": {
        "en": "Add Custom Font",
        "ru": "Добавить свой шрифт",
    },
    "font_imported_toast": {
        "en": "Font '{name}' installed and selected!",
        "ru": "Шрифт '{name}' успешно добавлен и выбран!",
    },
    "font_size_label": {
        "en": "Font Size:",
        "ru": "Размер шрифта:",
    },
    "uppercase_toggle": {
        "en": "ALL UPPERCASE (REELS STYLE)",
        "ru": "ВСЕ ЗАГЛАВНЫЕ (СТИЛЬ REELS)",
    },
    "bold_toggle": {
        "en": "Bold Typography",
        "ru": "Жирный шрифт (Bold)",
    },
    "max_width_ratio_label": {
        "en": "Max text width boundary:",
        "ru": "Максимальная ширина строки:",
    },

    # ── Colors & Effects ──
    "primary_color_label": {
        "en": "Text Color:",
        "ru": "Цвет основного текста:",
    },
    "outline_color_label": {
        "en": "Outline Color:",
        "ru": "Цвет контура букв:",
    },
    "outline_width_label": {
        "en": "Outline Thickness:",
        "ru": "Толщина контура:",
    },
    "shadow_offset_label": {
        "en": "Shadow Depth:",
        "ru": "Глубина тени:",
    },
    "background_box_toggle": {
        "en": "Background Banner Box",
        "ru": "Фоновая подложка под весь блок",
    },
    "bg_box_color_label": {
        "en": "Background Box Color:",
        "ru": "Цвет подложки:",
    },

    # ── Karaoke Animations ──
    "karaoke_section_label": {
        "en": "🔥 Word-by-Word Animations (Karaoke):",
        "ru": "🔥 Трендовые анимации слов (Shorts/Reels):",
    },
    "anim_pill": {
        "en": "📦 Pill Badge (Hormozi / CapCut)",
        "ru": "📦 Плашка (Hormozi / CapCut)",
    },
    "anim_bounce": {
        "en": "🦘 Word Bounce (Hop)",
        "ru": "🦘 Подпрыг слова (Bounce)",
    },
    "anim_pop": {
        "en": "💥 Smooth Pop Scale",
        "ru": "💥 Плавное увеличение (Pop)",
    },
    "anim_pill_bounce": {
        "en": "📦🦘 Pill with Bounce",
        "ru": "📦🦘 Плашка с подпрыгом",
    },
    "anim_pill_pop": {
        "en": "📦💥 Pill + Pop Scale",
        "ru": "📦💥 Плашка + Увеличение",
    },
    "anim_wave": {
        "en": "🌊 Word Wave (Ripple)",
        "ru": "🌊 Волна по словам (Wave)",
    },
    "anim_color": {
        "en": "✨ Highlight Color (Static)",
        "ru": "✨ Яркий цвет (Static)",
    },
    "anim_none": {
        "en": "❌ No Animation (Static)",
        "ru": "❌ Без анимации (Статика)",
    },
    "pill_bg_color_label": {
        "en": "Pill Badge Background Color:",
        "ru": "Цвет плашки активного слова:",
    },
    "pill_text_color_label": {
        "en": "Pill Badge Text Color:",
        "ru": "Цвет текста внутри плашки:",
    },
    "highlight_word_color_label": {
        "en": "Active Word Highlight Color:",
        "ru": "Цвет выделения слова (без плашки):",
    },

    # ── Export Dialog ──
    "export_dialog_title": {
        "en": "Export Video & Subtitles",
        "ru": "Экспорт видео и субтитров",
    },
    "export_format_label": {
        "en": "Export Option:",
        "ru": "Формат экспорта:",
    },
    "opt_burn_video": {
        "en": "🎬 Burn Subtitles into Video (Hardsub MP4)",
        "ru": "🎬 Вшить субтитры в видео (Hardsub MP4)",
    },
    "opt_export_srt": {
        "en": "📄 Subtitle File (.SRT)",
        "ru": "📄 Файл субтитров (.SRT)",
    },
    "opt_export_ass": {
        "en": "✨ Advanced Subtitles (.ASS with Styles)",
        "ru": "✨ Стилизованные субтитры (.ASS)",
    },
    "export_start_btn": {
        "en": "Start Export",
        "ru": "Начать экспорт",
    },
    "export_cancel_btn": {
        "en": "Cancel",
        "ru": "Отмена",
    },
    "export_success": {
        "en": "Export completed successfully!\nSaved to: {path}",
        "ru": "Экспорт успешно завершён!\nСохранено в: {path}",
    },
}


class I18nManager:
    """Manages application localization with persistent preferences."""

    def __init__(self) -> None:
        self._current_lang = LANG_EN
        self._listeners: list[Any] = []
        self._load_config()

    def _load_config(self) -> None:
        try:
            if os.path.exists(_CONFIG_PATH):
                with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._current_lang = data.get("language", LANG_EN)
        except Exception:
            self._current_lang = LANG_EN

    def _save_config(self) -> None:
        try:
            data = {}
            if os.path.exists(_CONFIG_PATH):
                try:
                    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data["language"] = self._current_lang
            with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_language(self) -> str:
        return self._current_lang

    def set_language(self, lang: str) -> None:
        if lang in (LANG_EN, LANG_RU) and lang != self._current_lang:
            self._current_lang = lang
            self._save_config()
            for cb in self._listeners:
                try:
                    cb(lang)
                except Exception:
                    pass

    def add_listener(self, cb: Any) -> None:
        if cb not in self._listeners:
            self._listeners.append(cb)

    def t(self, key: str, **kwargs) -> str:
        """Translate key into current language with optional format variables."""
        entry = TRANSLATIONS.get(key)
        if not entry:
            return key
        text = entry.get(self._current_lang, entry.get(LANG_EN, key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text


# Global singleton instance
i18n = I18nManager()


def t(key: str, **kwargs) -> str:
    """Convenient shortcut for translating keys."""
    return i18n.t(key, **kwargs)
