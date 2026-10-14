"""
Tests for Vitupi CLI arguments parsing and subcommands.
"""

import pytest
from vitupi.cli import build_parser, main
from vitupi.config import DomainPreset, ExtractionMode, VitupiConfig


def test_cli_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["extract", "dummy_video.mp4"])
    assert args.command == "extract"
    assert args.input == "dummy_video.mp4"
    assert args.output == "photos"
    assert args.mode == "balanced"
    assert args.preset == "default"
    assert args.fps is None
    assert args.max_photos == 100


def test_cli_parser_fine_grained_overrides():
    parser = build_parser()
    args = parser.parse_args([
        "extract", "my_vid.mp4",
        "-o", "custom_out",
        "-m", "exhaustive",
        "-p", "portrait",
        "--fps", "3.5",
        "--dense-fps", "8.0",
        "-s", "0.025",
        "--min-sharpness", "35.0",
        "--min-distance", "0.4",
        "--max-gap", "1.2",
        "--dedup-threshold", "4",
        "--max-photos", "50",
    ])
    assert args.command == "extract"
    assert args.fps == 3.5
    assert args.dense_fps == 8.0
    assert args.novelty_threshold == 0.025
    assert args.min_sharpness == 35.0
    assert args.min_distance == 0.4
    assert args.max_gap == 1.2
    assert args.dedup_threshold == 4
    assert args.max_photos == 50


def test_cli_gui_subcommand():
    parser = build_parser()
    args = parser.parse_args(["gui", "optional_sample.mp4"])
    assert args.command == "gui"
    assert args.video == "optional_sample.mp4"

    args_no_vid = parser.parse_args(["gui"])
    assert args_no_vid.command == "gui"
    assert args_no_vid.video is None
