# Vitupi (V2P)

**Video to Photos** — Intelligent, content-aware photograph extraction from videos.

Vitupi extracts visually distinct, high-quality photographs from videos by analyzing visual significance, novelty, and quality rather than relying on fixed-time intervals.

## Core Features
- **Visual Novelty over Fixed Intervals:** Extracts photos when meaningful content changes occur (pans, reveals, subject movement).
- **Scene-Boundary Detection:** Automatically segments videos into shots.
- **Adaptive Temporal Sampling:** Fast, sparse scanning during static shots; dense sampling during dynamic action.
- **Image Quality Scoring:** Ranks candidate frames based on sharpness, exposure, and composition.
- **Near-Duplicate Suppression:** Perceptual deduplication ensures varied, diverse photo collections.
- **Domain Presets:** Tailored modes for **Sports** (action peaks), **Security** (forensic CCTV motion), and **Candid** (facial flattery & anti-blink).
- **100% Local & Private:** Runs entirely on CPU without mandatory cloud or GPU dependencies.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from vitupi import extract_photos

result = extract_photos("video.mp4", output_dir="photos/")
print(f"Extracted {len(result.photos)} photographs.")
```

CLI:
```bash
vitupi extract video.mp4 --output photos/ --preset candid
```
