"""
Performance and Quality Benchmarking Suite for Vitupi.
Calculates extraction throughput (FPS), deduplication efficiency, scene coverage, and score distributions.
"""

from dataclasses import dataclass
import json
import os
import tempfile
import time
from typing import Any, Dict, Optional

from vitupi.config import VitupiConfig
from vitupi.models import ExtractionResult
from vitupi.pipeline import ExtractionPipeline


@dataclass
class BenchmarkReport:
    """Formal performance, throughput, and selection quality benchmark result."""

    source_video: str
    duration_sec: float
    resolution: str
    processing_time_sec: float
    fps: float
    speed_factor: float
    total_frames: int
    frames_decoded: int
    scenes_detected: int
    candidates_evaluated: int
    duplicates_suppressed: int
    duplicate_suppression_rate_pct: float
    photos_exported: int
    scene_coverage_pct: float
    mean_quality_score: float
    max_quality_score: float
    min_quality_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert benchmark report metrics to a serializable dictionary."""
        return {
            "source_video": self.source_video,
            "duration_sec": round(self.duration_sec, 2),
            "resolution": self.resolution,
            "processing_time_sec": round(self.processing_time_sec, 3),
            "fps": round(self.fps, 1),
            "speed_factor": round(self.speed_factor, 2),
            "total_frames": self.total_frames,
            "frames_decoded": self.frames_decoded,
            "scenes_detected": self.scenes_detected,
            "candidates_evaluated": self.candidates_evaluated,
            "duplicates_suppressed": self.duplicates_suppressed,
            "duplicate_suppression_rate_pct": round(self.duplicate_suppression_rate_pct, 1),
            "photos_exported": self.photos_exported,
            "scene_coverage_pct": round(self.scene_coverage_pct, 1),
            "mean_quality_score": round(self.mean_quality_score, 2),
            "max_quality_score": round(self.max_quality_score, 2),
            "min_quality_score": round(self.min_quality_score, 2),
        }

    def to_json(self, file_path: str) -> str:
        """Write benchmark data to a formatted JSON file."""
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return file_path

    def format_table(self) -> str:
        """Render a clean, professional ASCII metric summary table (zero emojis)."""
        lines = [
            "+------------------------------------------------------------+",
            "|                VITUPI BENCHMARK REPORT                    |",
            "+------------------------------------------------------------+",
            f"| Source Video        : {os.path.basename(self.source_video):<36} |",
            f"| Resolution          : {self.resolution:<36} |",
            f"| Video Duration      : {self.duration_sec:<6.2f} sec                          |",
            "+------------------------------------------------------------+",
            "| PERFORMANCE & THROUGHPUT                                   |",
            "+------------------------------------------------------------+",
            f"| Elapsed Wall-Clock  : {self.processing_time_sec:<6.2f} sec                          |",
            f"| Frames Decoded      : {self.frames_decoded:<6} of {self.total_frames:<6}                   |",
            f"| Processing Speed    : {self.fps:<6.1f} FPS                           |",
            f"| Realtime Multiplier : {self.speed_factor:<6.2f}x                           |",
            "+------------------------------------------------------------+",
            "| QUALITY & SELECTION METRICS                                |",
            "+------------------------------------------------------------+",
            f"| Scenes Detected     : {self.scenes_detected:<6}                                 |",
            f"| Scene Coverage      : {self.scene_coverage_pct:<6.1f}%                              |",
            f"| Candidates Evaluated: {self.candidates_evaluated:<6}                                 |",
            f"| Duplicates Purged   : {self.duplicates_suppressed:<6} ({self.duplicate_suppression_rate_pct:.1f}%)                   |",
            f"| Photos Exported     : {self.photos_exported:<6}                                 |",
            f"| Mean Quality Score  : {self.mean_quality_score:<6.2f} / 100                        |",
            f"| Quality Range       : [{self.min_quality_score:.1f} - {self.max_quality_score:.1f}]                      |",
            "+------------------------------------------------------------+",
        ]
        return "\n".join(lines)


def run_benchmark(
    video_path: str,
    config: Optional[VitupiConfig] = None,
    output_dir: Optional[str] = None,
) -> BenchmarkReport:
    """Execute a comprehensive benchmark on a video file.

    Args:
        video_path: Path to target video file.
        config: Vitupi configuration options.
        output_dir: Directory where test photos are temporarily or permanently saved.

    Returns:
        BenchmarkReport with performance and quality analytics.
    """
    cfg = config or VitupiConfig()
    use_temp = output_dir is None

    if use_temp:
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="vitupi_bench_")
        target_dir = temp_dir_obj.name
    else:
        target_dir = output_dir

    try:
        start_time = time.perf_counter()
        pipeline = ExtractionPipeline(config=cfg)
        result: ExtractionResult = pipeline.run(video_path, output_dir=target_dir)
        total_time = max(1e-4, time.perf_counter() - start_time)

        meta = result.metadata
        stats = result.statistics

        frames_decoded = stats.frames_decoded or stats.total_frames_in_video
        fps = frames_decoded / total_time
        speed_factor = meta.duration_sec / total_time if meta.duration_sec > 0 else 0.0

        candidates = max(1, stats.candidates_generated)
        suppressed = stats.duplicates_suppressed
        suppression_rate = (suppressed / candidates) * 100.0

        scenes_total = max(1, stats.scenes_detected)
        covered_scenes = len(set(p.scene_id for p in result.photos))
        coverage_pct = min(100.0, (covered_scenes / scenes_total) * 100.0)

        scores = [
            (p.quality_score * 100.0 if p.quality_score <= 1.0 else p.quality_score)
            for p in result.photos
        ]
        mean_score = sum(scores) / len(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0
        min_score = min(scores) if scores else 0.0

        report = BenchmarkReport(
            source_video=video_path,
            duration_sec=meta.duration_sec,
            resolution=f"{meta.width}x{meta.height}",
            processing_time_sec=total_time,
            fps=fps,
            speed_factor=speed_factor,
            total_frames=meta.total_frames,
            frames_decoded=frames_decoded,
            scenes_detected=stats.scenes_detected,
            candidates_evaluated=stats.candidates_generated,
            duplicates_suppressed=suppressed,
            duplicate_suppression_rate_pct=suppression_rate,
            photos_exported=len(result.photos),
            scene_coverage_pct=coverage_pct,
            mean_quality_score=mean_score,
            max_quality_score=max_score,
            min_quality_score=min_score,
        )
        return report
    finally:
        if use_temp:
            try:
                temp_dir_obj.cleanup()
            except Exception:
                pass
