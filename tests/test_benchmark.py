"""
Tests for Vitupi Benchmark engine and reporting.
"""

import os
import json
import numpy as np
import pytest
from .test_pipeline import create_synthetic_video
from vitupi.benchmark import BenchmarkReport, run_benchmark
from vitupi.config import VitupiConfig


def test_benchmark_synthetic_video(tmp_path):
    video_path = str(tmp_path / "bench_video.mp4")
    create_synthetic_video(video_path, fps=24.0, num_frames=72)

    config = VitupiConfig(base_fps=2.0, dense_fps=4.0)
    report = run_benchmark(video_path, config=config)

    assert isinstance(report, BenchmarkReport)
    assert report.total_frames == 72
    assert report.fps > 0.0
    assert report.processing_time_sec > 0.0
    assert report.photos_exported > 0
    assert 0.0 <= report.scene_coverage_pct <= 100.0
    assert 0.0 <= report.duplicate_suppression_rate_pct <= 100.0

    # Test ASCII format table
    table_str = report.format_table()
    assert "VITUPI BENCHMARK REPORT" in table_str
    assert "PERFORMANCE & THROUGHPUT" in table_str
    assert "QUALITY & SELECTION METRICS" in table_str

    # Test JSON export
    json_path = str(tmp_path / "report.json")
    report.to_json(json_path)
    assert os.path.exists(json_path)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["source_video"] == video_path
    assert data["photos_exported"] == report.photos_exported
