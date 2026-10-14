# Vitupi (V2P)

**Video to Photos** — Intelligent, content-aware photograph extraction studio from videos.

Vitupi extracts visually distinct, high-quality photographs from videos by analyzing visual significance, novelty, and quality rather than relying on dumb fixed-time intervals. It comes with both a powerful CLI and a desktop PyQt6 GUI Studio featuring an MS Word–style ribbon and side-by-side candidate comparison.

---

## Key Highlights

- **Visual Novelty over Fixed Intervals:** Detects and captures key moments when meaningful visual changes occur (camera pans, subject reveals, expressions, dynamic movements).
- **Domain Presets:**
  - `portrait` / `candid`: Optimized for people, facial flattery, smiling expressions, and high facial sharpness.
  - `sports`: Captures high-energy kinematic action peaks and athletic postures.
  - `security`: Forensic CCTV motion and presence capture.
  - `default`: Balanced multi-purpose extraction.
- **Perceptual Deduplication:** Burst-aware perceptual hashing prevents near-identical photos while preserving distinct expressions.
- **Granular Parameter Control:** Full control over coarse and dense sampling rates, sensitivity thresholds, focus/sharpness cutoffs, and temporal gaps.
- **Desktop GUI Studio (PyQt6):**
  - **MS Word–Style Ribbon:** Tabbed control panel organizing quick extraction, parameter tuning, selection/review tools, and custom export options.
  - **Gallery Grid View:** Interactive cards with timestamps, sharpness badges, and selection checkboxes.
  - **A/B Side-by-Side Comparator:** Inspect similar candid expressions side-by-side with metric diffs and single-click decision tools (`Keep Only A`, `Keep Only B`, `Keep Both`).
- **100% Local & Private:** Runs entirely on your CPU/local hardware without cloud dependencies.

---

## Installation & Distribution

### 1. Distributable Wheel (`.whl`)
Vitupi is packaged as a standard Python wheel in `dist/vitupi-0.1.0-py3-none-any.whl`:

```bash
# Core CLI and library
pip install dist/vitupi-0.1.0-py3-none-any.whl

# Include PyQt6 Desktop GUI
pip install dist/vitupi-0.1.0-py3-none-any.whl[gui]
```

### 2. Developer / Editable Install
```bash
git clone https://github.com/mizzrayush/vitupi.git
cd vitupi
pip install -e .[all]
```

---

## Graphical User Interface (GUI Studio)

Launch the desktop application via:

```bash
# Via console script
vitupi-gui

# Or via the CLI launcher
vitupi gui

# Pre-load a video directly into the GUI
vitupi gui path/to/video.mp4
```

### GUI Features

1. **Top Ribbon Tab Panel (MS Word Style):**
   - 🚀 **Home & Extract:** Select video source and output folder, choose preset profile and mode, set maximum photos, monitor live extraction progress, and cancel background tasks.
   - ⚙️ **Parameters & Tuning:** Sliders and spinboxes to fine-tune Base FPS, Dense Burst FPS, Novelty Sensitivity Threshold, Min Sharpness Score, Min Distance between frames, Max Temporal Gap, Perceptual Hash Hamming Threshold, and feature toggles.
   - 🔍 **Review & Compare:** Switch views between the Gallery Grid and the A/B Side-by-Side Comparator; perform batch selections (Select All, Deselect All, Invert); filter photos interactively using the live Sharpness Cutoff slider.
   - 💾 **Export & Output:** Choose export format (PNG, JPEG, WebP, TIFF), adjust JPEG/WebP compression quality, toggle Contact Sheets and JSON reports, and export selected photos with one click.

2. **Central Interactive Canvas:**
   - **Interactive Gallery:** Grid of photo cards displaying frame index, timestamp, and sharpness score. Quickly route any photo to Slot A or Slot B for comparison.
   - **A/B Side-by-Side Comparator:** Compare two candidate frames side-by-side with metric comparisons (sharpness, novelty, dimensions) and instant resolution buttons (`Keep Only A`, `Keep Only B`, `Keep Both`).

---

## Command-Line Interface (CLI)

### Basic Extraction
```bash
vitupi extract video.mp4 --output photos/ --preset portrait
```

### Fine-Grained Parameter Tuning
```bash
vitupi extract video.mp4 \
  --output candids/ \
  --preset portrait \
  --fps 2.0 \
  --dense-fps 6.0 \
  --sensitivity 0.03 \
  --min-sharpness 25.0 \
  --min-distance 0.5 \
  --max-gap 1.5 \
  --dedup-threshold 6 \
  --max-photos 50
```

### Batch Directory Processing
```bash
vitupi extract /path/to/videos/ --output /path/to/extracted/ --preset candid
```

---

## Python API

```python
from vitupi import extract_photos, VitupiConfig, DomainPreset, ExtractionMode

config = VitupiConfig(
    preset=DomainPreset.PORTRAIT,
    mode=ExtractionMode.BALANCED,
    base_fps=2.0,
    dense_fps=6.0,
    novelty_threshold=0.03,
    min_sharpness_score=25.0,
    max_photos=50,
)

result = extract_photos("video.mp4", output_dir="my_candids/", config=config)

print(f"Extracted {len(result.photos)} photographs.")
print(f"Contact sheet: {result.contact_sheet_path}")
print(f"JSON Report: {result.report_path}")
```

---

## Architecture

```
vitupi/
├── api.py               # Top-level API entry points
├── cli.py               # Command-line interface and subcommands
├── config.py            # Dataclass configuration and presets
├── models.py            # Metadata, Candidate, and Result schemas
├── pipeline.py          # Unified multi-stage extraction pipeline
├── detection/           # Shot cut and visual novelty detection
├── sampling/            # Adaptive temporal and burst sampling
├── scoring/             # Multi-metric composite quality scoring
├── selection/           # Temporal clustering and ranking
├── deduplication/       # Perceptual hash near-duplicate suppression
├── export/              # Image writer, contact sheet, and JSON reports
├── gui/                 # Desktop PyQt6 GUI Studio
│   ├── app.py           # Application entry point and launcher
│   ├── main_window.py   # Main window and layout manager
│   ├── ribbon.py        # MS Word-style top tab panel
│   ├── canvas.py        # Gallery grid and A/B side-by-side comparator
│   └── worker.py        # Background extraction QThread
└── video/               # High-performance OpenCV video decoding
```

---

## License

Apache-2.0
