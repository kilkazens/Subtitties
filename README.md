# 🎬 Subtitties - Modern AI Subtitles & Reels Editor

<p align="center">
  <img src="logo.ico" width="128" height="128" alt="Subtitties Logo" />
</p>

<p align="center">
  <strong>Fast, elegant desktop application for generating viral TikTok, Instagram Reels, and YouTube Shorts subtitles with AI speech recognition and dynamic word-by-word animations.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#word-animations">Word Animations</a> •
  <a href="#custom-fonts">Custom Fonts</a> •
  <a href="#presets">Presets</a> •
  <a href="#settings">Settings</a>
</p>

---

## 🌟 Features

- **🎙️ Fast Local AI Speech-to-Text:**
  - Powered by `faster-whisper` (CTranslate2) with GPU (NVIDIA CUDA) or multi-threaded CPU.
  - Automatic Voice Activity Detection (Silero VAD) to eliminate silent gaps.
  - Word-level timestamps for precise word-by-word karaoke synchronization.
  - Automatic dynamic chunking into punchy 3-5 word Reels phrases.

- **🔥 Dynamic Word-by-Word Karaoke Animations:**
  - **📦 Pill Badge (Hormozi / CapCut):** Sleek colored badge behind the spoken word with zero character overlap.
  - **🦘 Word Bounce (Hop):** Smooth half-sine jump on the peak of the spoken word.
  - **💥 Smooth Pop Scale:** Elastic punch-in growth (up to 1.25x) and smooth return.
  - **📦🦘 Pill with Bounce:** Pill and active word jump together with the beat.
  - **📦💥 Pill + Pop Scale:** Pill and active word smoothly expand together.
  - **🌊 Word Wave (Ripple):** Spoken word bounces with trailing wave ripple on adjacent words.
  - **✨ Highlight Color:** Instant vibrant color change.

- **🔤 Custom Font Importer:**
  - Bundled with top trending fonts (Unbounded, Press Start 2P, Geologica, Onest, Russo One, Rubik Mono One, Comfortaa, Golos Text, Dela Gothic One, Montserrat Black, Bebas Neue, Oswald).
  - **1-Click Font Import:** Easily import your own `.ttf` or `.otf` fonts! The app installs them, adds them to the live WYSIWYG font picker, and persists them across sessions.

- **💾 Custom Preset Management:**
  - Save your favorite subtitle styling (fonts, colors, outlines, shadows, pills, animations, boundaries) as custom presets.
  - User presets appear at the top with a ⭐ badge and can be edited or deleted anytime.

- **⚡ Buttery Smooth 60 FPS Video Preview:**
  - Hardware-accelerated OpenCV frame processing offloaded to background threads.
  - Frame drop guard ensuring 0% UI lag and perfect audio/video synchronization.
  - Magnetic grid snapping (center, thirds, margins, standard Reels 85% bottom safety line).
  - Interactive mouse dragging to position subtitles anywhere directly on the video.

- **🌐 Internationalization (English & Russian):**
  - **English as default** language.
  - One-click toggle to **Russian (Русский)** in Settings.

- **🎬 Multi-Format Export:**
  - **Hardsub Video:** Burns subtitles directly into high-quality MP4 using hardware-optimized FFmpeg.
  - **SRT File:** Standard industry subtitle file.
  - **ASS File:** Advanced SubStation Alpha with precise position tags, fonts, and styles.

---

## 🚀 Quick Start (Windows)

1. **Launch via Desktop Shortcut:**
   Double-click the created **`Subtitties`** shortcut on your Desktop or run:
   ```cmd
   Subtitties.bat
   ```

2. **Manual Python Launch:**
   ```bash
   git clone https://github.com/DoctorTeshka/Subtitties.git
   cd Subtitties
   pip install -r requirements.txt
   python app.py
   ```

---

## 📦 Requirements

- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.14)
- **FFmpeg** (automatically detected from system PATH or included binary)
- **Dependencies:**
  - `customtkinter`
  - `opencv-python`
  - `pillow`
  - `faster-whisper`
  - `pygame-ce`
  - `fonttools`
  - `numpy`

Install all dependencies in one command:
```bash
pip install customtkinter opencv-python pillow faster-whisper pygame-ce fonttools numpy
```

---

## 🎨 Word Animations Showcase

| Mode | Visual Effect | Description |
|------|---------------|-------------|
| **`📦 Pill Badge`** | Rounded background badge | High-contrast pill behind the active spoken word with baseline alignment |
| **`🦘 Word Bounce`** | Vertical jump $\Delta y = -\sin(\pi \cdot p)$ | Dynamic hop that peaks mid-word and lands smoothly back on the line |
| **`💥 Smooth Pop`** | Radial zoom $1.0 \to 1.25 \to 1.0$ | Punchy zoom effect popular in Alex Hormozi and MrBeast videos |
| **`📦🦘 Pill + Bounce`** | Pill badge + jump | Both the pill and the active text jump together rhythmically |
| **`📦💥 Pill + Pop`** | Pill badge + zoom | Pill and text smoothly scale up together |
| **`🌊 Word Wave`** | Cascade wave | Active word hops and triggers a ripple effect on adjacent words |

---

## ⚙️ Settings & Configuration

Click the **`⚙️ Settings`** button on the top toolbar to:
- Switch application language between **English** (default) and **Russian**.
- View application version, installed custom fonts, and system info.

---

## 📁 Project Structure

```text
Subtitties/
├── app.py                   # Main GUI application window and controller
├── Subtitties.bat           # Quick launcher script for Windows
├── logo.ico                 # High-resolution application icon
├── requirements.txt         # Python dependencies
├── core/
│   ├── i18n.py              # Internationalization engine (EN/RU)
│   ├── recognizer.py        # faster-whisper AI speech-to-text integration
│   ├── subtitle.py          # SubtitleSegment and SubtitleStyle dataclasses
│   ├── presets.py           # Curated Reels presets & font registration
│   └── exporter.py          # FFmpeg hardsub burner, SRT, and ASS exporter
├── ui/
│   ├── icons.py             # Vector anti-aliased icon generator
│   ├── video_player.py      # 60 FPS SIMD canvas player & karaoke renderer
│   ├── subtitle_editor.py   # Interactive subtitle segments table
│   ├── style_panel.py       # Typography, WYSIWYG font picker & styling
│   ├── settings_dialog.py   # Language and settings modal dialog
│   └── export_dialog.py     # Export configuration & progress modal
└── assets/
    ├── fonts/               # Bundled Cyrillic & trending Reels fonts
    ├── user_presets.json    # User-created custom presets
    └── custom_fonts.json    # User-imported custom fonts
```

---

## 📄 License

MIT License. Free for commercial and personal video editing.
