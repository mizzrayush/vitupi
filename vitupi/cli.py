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

    extract_cmd = subparsers.add_parser("extract", help="Extract photographs from a video or directory of videos.")
    extract_cmd.add_argument("input", help="Path to a video file or a directory of videos.")
    extract_cmd.add_argument(
        "-o", "--output",
        default="photos",
        help="Destination directory for extracted photographs (default: photos/)",
    )
    extract_cmd.add_argument(
        "-m", "--mode",
        choices=["conservative", "balanced", "exhaustive"],
        default="balanced",
        help="Extraction density mode (default: balanced)",
    )
    extract_cmd.add_argument(
        "-p", "--preset",
        choices=["default", "sports", "security", "candid"],
        default="default",
        help="Domain-specific preset (default: default)",
    )
    extract_cmd.add_argument(
        "--max-photos",
        type=int,
        default=100,
        help="Maximum number of photographs to extract (default: 100)",
    )
    extract_cmd.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable near-duplicate perceptual suppression.",
    )
    extract_cmd.add_argument(
        "--no-contact-sheet",
        action="store_true",
        help="Disable overview contact sheet generation.",
    )
    extract_cmd.add_argument(
        "--no-scene-detection",
        action="store_true",
        help="Disable shot/scene boundary detection.",
    )

    return parser


def process_single_video(video_path: str, output_dir: str, config: VitupiConfig) -> int:
    print(f"\nProcessing: {video_path}")
    print(f"Output directory: {output_dir}")
    print(f"Mode: {config.mode.value} | Preset: {config.preset.value}")

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
        config = VitupiConfig(
            mode=ExtractionMode(args.mode),
            preset=DomainPreset(args.preset),
            max_photos=args.max_photos,
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
