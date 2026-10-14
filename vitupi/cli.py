"""
Command-line interface for Vitupi.
"""

import argparse
import os
import sys
import time
from typing import List

from vitupi.api import extract_photos
from vitupi.config import DomainPreset, ExtractionMode, VitupiConfig


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vitupi",
        description="Vitupi: Intelligent, content-aware photograph extraction from videos.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_cmd = subparsers.add_parser(
        "extract",
        help="Extract photographs from a video or directory of videos.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    extract_cmd.add_argument("input", help="Path to a video file or a directory of videos.")
    extract_cmd.add_argument(
        "-o", "--output",
        default="photos",
        help="Destination directory for extracted photographs.",
    )
    extract_cmd.add_argument(
        "-m", "--mode",
        choices=["conservative", "balanced", "exhaustive"],
        default="balanced",
        help="Extraction density mode.",
    )
    extract_cmd.add_argument(
        "-p", "--preset",
        choices=["default", "sports", "security", "candid", "portrait"],
        default="default",
        help="Domain-specific preset.",
    )
    extract_cmd.add_argument(
        "--max-photos",
        type=int,
        default=100,
        help="Maximum number of photographs to extract (0 or -1 for unlimited).",
    )

    # Granular sampling and threshold controls
    tuning_group = extract_cmd.add_argument_group("Fine-grained Extraction Controls")
    tuning_group.add_argument(
        "--fps", "--base-fps",
        dest="fps",
        type=float,
        default=None,
        help="Coarse sampling rate in frames/sec (e.g. --fps 2.0). Overrides preset/mode default.",
    )
    tuning_group.add_argument(
        "--dense-fps",
        type=float,
        default=None,
        help="Burst sampling rate in frames/sec around visual events (e.g. --dense-fps 6.0).",
    )
    tuning_group.add_argument(
        "-s", "--sensitivity", "--novelty-threshold",
        dest="novelty_threshold",
        type=float,
        default=None,
        help="Visual change sensitivity threshold [0.0 - 1.0]. Lower values capture subtler movements (e.g. -s 0.03).",
    )
    tuning_group.add_argument(
        "--min-sharpness",
        type=float,
        default=None,
        help="Minimum Laplacian variance required for an exported photo (e.g. --min-sharpness 20.0).",
    )
    tuning_group.add_argument(
        "--min-distance",
        type=float,
        default=None,
        help="Minimum temporal distance in seconds between consecutive exported photos (e.g. --min-distance 0.5).",
    )
    tuning_group.add_argument(
        "--max-gap",
        type=float,
        default=None,
        help="Maximum seconds in a continuous shot before forcing candidate evaluation (e.g. --max-gap 1.5).",
    )
    tuning_group.add_argument(
        "--dedup-threshold",
        type=int,
        default=None,
        help="Perceptual hash Hamming distance for duplicate suppression within bursts (e.g. --dedup-threshold 6).",
    )
    tuning_group.add_argument(
        "--scene-threshold",
        type=float,
        default=None,
        help="PySceneDetect cut detection sensitivity (default: 27.0).",
    )

    # Feature flags
    feature_group = extract_cmd.add_argument_group("Feature Toggles")
    feature_group.add_argument(
        "--flattery",
        action="store_true",
        default=None,
        help="Force facial flattery and portrait sharpness enhancement on.",
    )
    feature_group.add_argument(
        "--no-flattery",
        action="store_false",
        dest="flattery",
        help="Disable facial flattery enhancement.",
    )
    feature_group.add_argument(
        "--action-peaks",
        action="store_true",
        default=None,
        help="Force kinematic action-peak detection on.",
    )
    feature_group.add_argument(
        "--no-action-peaks",
        action="store_false",
        dest="action_peaks",
        help="Disable kinematic action-peak detection.",
    )
    feature_group.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable near-duplicate perceptual suppression entirely.",
    )
    feature_group.add_argument(
        "--no-contact-sheet",
        action="store_true",
        help="Disable overview contact sheet generation.",
    )
    feature_group.add_argument(
        "--no-scene-detection",
        action="store_true",
        help="Disable shot/scene boundary detection.",
    )

    return parser


def process_single_video(video_path: str, output_dir: str, config: VitupiConfig) -> int:
    print(f"\nProcessing: {video_path}")
    print(f"Output directory: {output_dir}")
    print(f"Mode: {config.mode.value} | Preset: {config.preset.value}")
    print(f"Sampling: base={config.base_fps} fps, dense={config.dense_fps} fps, max_gap={config.max_temporal_gap}s, min_dist={config.min_temporal_distance}s")
    print(f"Thresholds: sensitivity={config.novelty_threshold}, min_sharpness={config.min_sharpness_score}, dedup={config.dedup_threshold}")

    try:
        t0 = time.time()
        result = extract_photos(video_path, output_dir=output_dir, config=config)
        elapsed = time.time() - t0

        print(f"Success: Extracted {len(result.photos)} photographs in {elapsed:.2f}s")
        print(f"  - Scenes detected: {result.statistics.scenes_detected}")
        print(f"  - Candidates evaluated: {result.statistics.candidates_generated}")
        print(f"  - Duplicates suppressed: {result.statistics.duplicates_suppressed}")
        print(f"  - Low quality filtered: {result.statistics.low_quality_filtered}")
        if result.contact_sheet_path:
            print(f"  - Contact sheet: {result.contact_sheet_path}")
        if result.report_path:
            print(f"  - JSON report: {result.report_path}")
        return 0
    except Exception as e:
        print(f"Error processing {video_path}: {e}", file=sys.stderr)
        return 1


def main(argv: List[str] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "extract":
        target = args.input
        max_photos = None if (args.max_photos is not None and args.max_photos <= 0) else args.max_photos

        config = VitupiConfig(
            mode=ExtractionMode(args.mode),
            preset=DomainPreset(args.preset),
            max_photos=max_photos,
            base_fps=args.fps,
            dense_fps=args.dense_fps,
            novelty_threshold=args.novelty_threshold,
            min_sharpness_score=args.min_sharpness,
            min_temporal_distance=args.min_distance,
            max_temporal_gap=args.max_gap,
            dedup_threshold=args.dedup_threshold,
            scene_threshold=args.scene_threshold,
            flattery_filter=args.flattery,
            action_peak_detection=args.action_peaks,
            duplicate_removal=not args.no_dedup,
            generate_contact_sheet=not args.no_contact_sheet,
            scene_detection=not args.no_scene_detection,
        )

        if os.path.isfile(target):
            return process_single_video(target, args.output, config)
        elif os.path.isdir(target):
            # Batch directory processing
            video_files = [
                os.path.join(target, f)
                for f in sorted(os.listdir(target))
                if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS
            ]
            if not video_files:
                print(f"No video files found in directory: {target}", file=sys.stderr)
                return 1

            print(f"Found {len(video_files)} video(s) to process in batch mode.")
            failures = 0
            for vid in video_files:
                base_name = os.path.splitext(os.path.basename(vid))[0]
                vid_out = os.path.join(args.output, base_name)
                res = process_single_video(vid, vid_out, config)
                if res != 0:
                    failures += 1

            print(f"\nBatch processing complete. Total: {len(video_files)}, Failures: {failures}")
            return 0 if failures == 0 else 1
        else:
            print(f"Input path does not exist: {target}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
