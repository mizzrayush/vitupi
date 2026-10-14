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
    subparsers = parser.add_subparsers(dest="command", required=False)

    # GUI subcommand
    gui_cmd = subparsers.add_parser(
        "gui",
        help="Launch the interactive PyQt6 graphical user interface with MS Word-style ribbon and A/B comparison.",
    )
    gui_cmd.add_argument(
        "video",
        nargs="?",
        default=None,
        help="Optional initial video path to load in the GUI.",
    )

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
        default="default",
        help="Domain-specific preset ('default', 'sports', 'security', 'candid', 'portrait', 'custom', or saved custom preset).",
    )
    extract_cmd.add_argument(
        "--max-photos",
        type=int,
        default=100,
        help="Maximum number of photographs to extract (0 or -1 for unlimited).",
    )
    extract_cmd.add_argument(
        "-j", "--workers",
        type=int,
        default=None,
        help="Number of concurrent worker threads for parallel batch processing (default: CPU count).",
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
    tuning_group.add_argument(
        "--motion-blur-penalty",
        type=float,
        default=None,
        help="Multiplier penalizing high motion-blur frames (default: 1.0; e.g. 1.5).",
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
    feature_group.add_argument(
        "--no-adaptive-sampling",
        action="store_true",
        help="Disable adaptive burst sampling (sample strictly at base FPS).",
    )
    feature_group.add_argument(
        "--no-quality-scoring",
        action="store_true",
        help="Disable composite quality and sharpness scoring.",
    )

    # Presets Subcommand
    presets_cmd = subparsers.add_parser(
        "presets",
        help="List, inspect, save, and manage extraction presets (both built-in and persistent custom presets).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    presets_cmd.add_argument(
        "-l", "--list",
        action="store_true",
        help="List all built-in and persistent custom presets.",
    )
    presets_cmd.add_argument(
        "--show",
        metavar="PRESET",
        help="Show detailed configuration parameters for a specific preset.",
    )
    presets_cmd.add_argument(
        "--save",
        metavar="NAME",
        help="Save current parameter settings as a named custom preset to disk.",
    )
    presets_cmd.add_argument(
        "--delete",
        metavar="NAME",
        help="Delete a user-saved custom preset from disk.",
    )
    presets_cmd.add_argument("--fps", type=float, default=None, help="Base scan FPS for saved preset.")
    presets_cmd.add_argument("--dense-fps", type=float, default=None, help="Burst FPS for saved preset.")
    presets_cmd.add_argument("-s", "--sensitivity", type=float, default=None, help="Novelty sensitivity.")
    presets_cmd.add_argument("--min-sharpness", type=float, default=None, help="Min sharpness score.")
    presets_cmd.add_argument("--motion-blur-penalty", type=float, default=None, help="Motion blur penalty.")
    presets_cmd.add_argument("--flattery", action="store_true", default=None, help="Enable facial flattery.")
    presets_cmd.add_argument("--action-peaks", action="store_true", default=None, help="Enable action peak detection.")

    # Benchmark Subcommand
    bench_cmd = subparsers.add_parser(
        "benchmark",
        help="Run comprehensive performance, FPS throughput, deduplication, and quality benchmarks on a video.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    bench_cmd.add_argument("video", help="Path to video file to benchmark.")
    bench_cmd.add_argument(
        "-p", "--preset",
        default="default",
        help="Preset to evaluate during benchmark.",
    )
    bench_cmd.add_argument(
        "-m", "--mode",
        choices=["conservative", "balanced", "exhaustive"],
        default="balanced",
        help="Extraction mode to evaluate.",
    )
    bench_cmd.add_argument(
        "-o", "--output-json",
        default=None,
        help="Optional destination path to save JSON benchmark report.",
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

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "presets":
        from vitupi.presets import get_preset_manager
        pm = get_preset_manager()

        if args.delete:
            if pm.is_builtin(args.delete):
                print(f"Error: '{args.delete}' is a system built-in preset and cannot be deleted.", file=sys.stderr)
                return 1
            if pm.delete_preset(args.delete):
                print(f"Successfully deleted custom preset: '{args.delete}'")
                return 0
            else:
                print(f"Error: Custom preset '{args.delete}' not found.", file=sys.stderr)
                return 1

        if args.save:
            base_cfg = pm.get_preset_config("custom")
            save_dict = base_cfg.to_dict()
            if args.fps is not None:
                save_dict["base_fps"] = args.fps
            if args.dense_fps is not None:
                save_dict["dense_fps"] = args.dense_fps
            if args.sensitivity is not None:
                save_dict["novelty_threshold"] = args.sensitivity
            if args.min_sharpness is not None:
                save_dict["min_sharpness_score"] = args.min_sharpness
            if args.motion_blur_penalty is not None:
                save_dict["motion_blur_penalty"] = args.motion_blur_penalty
            if args.flattery is not None:
                save_dict["flattery_filter"] = args.flattery
            if args.action_peaks is not None:
                save_dict["action_peak_detection"] = args.action_peaks

            pm.save_preset(args.save, save_dict)
            print(f"Successfully saved custom preset: '{args.save}' to {pm.storage_file}")
            return 0

        if args.show:
            cfg = pm.get_preset_config(args.show)
            if not cfg:
                print(f"Error: Preset '{args.show}' not found.", file=sys.stderr)
                return 1
            is_built = pm.is_builtin(args.show)
            print(f"\nPreset: {args.show} ({'Built-in' if is_built else 'Custom Saved'})")
            print("-" * 50)
            for k, v in sorted(cfg.to_dict().items()):
                print(f"  {k:<26}: {v}")
            print("-" * 50)
            return 0

        # Default: list all presets in a clean table
        all_presets = pm.list_all_presets()
        print("\nVitupi Available Presets:")
        print(f"{'Preset Name':<18} {'Type':<12} {'Base FPS':<10} {'Burst FPS':<11} {'Novelty':<10} {'Min Focus':<11} {'Flattery'}")
        print("-" * 84)
        for name in all_presets:
            p_type = "Built-in" if pm.is_builtin(name) else "Custom"
            cfg = pm.get_preset_config(name)
            fps_str = f"{cfg.base_fps:.1f}" if cfg.base_fps else "auto"
            dense_str = f"{cfg.dense_fps:.1f}" if cfg.dense_fps else "auto"
            nov_str = f"{cfg.novelty_threshold:.3f}" if cfg.novelty_threshold else "auto"
            sharp_str = f"{cfg.min_sharpness_score:.1f}" if cfg.min_sharpness_score else "auto"
            flat_str = "Yes" if cfg.flattery_filter else "No"
            print(f"{name:<18} {p_type:<12} {fps_str:<10} {dense_str:<11} {nov_str:<10} {sharp_str:<11} {flat_str}")
        print("-" * 84)
        print("Use --preset <name> with 'vitupi extract' to run extraction with any preset.")
        print("Use 'vitupi presets --save <name>' to create new custom presets via CLI.\n")
        return 0

    if args.command == "gui":
        try:
            from vitupi.gui import launch_gui
            return launch_gui(initial_video=args.video)
        except ImportError as e:
            print(f"Error launching GUI: {e}\nPlease install PyQt6: pip install vitupi[gui]", file=sys.stderr)
            return 1

    if args.command == "extract":
        target = args.input
        max_photos = None if (args.max_photos is not None and args.max_photos <= 0) else args.max_photos

        from vitupi.presets import get_preset_manager

        pm = get_preset_manager()
        preset_cfg = pm.get_preset_config(args.preset)

        try:
            domain_preset = DomainPreset(args.preset.lower())
        except ValueError:
            domain_preset = DomainPreset.CUSTOM

        config = VitupiConfig(
            mode=ExtractionMode(args.mode),
            preset=domain_preset,
            custom_name=args.preset if domain_preset == DomainPreset.CUSTOM else None,
            max_photos=max_photos if max_photos is not None else preset_cfg.max_photos,
            base_fps=args.fps if args.fps is not None else preset_cfg.base_fps,
            dense_fps=args.dense_fps if args.dense_fps is not None else preset_cfg.dense_fps,
            novelty_threshold=args.novelty_threshold if args.novelty_threshold is not None else preset_cfg.novelty_threshold,
            min_sharpness_score=args.min_sharpness if args.min_sharpness is not None else preset_cfg.min_sharpness_score,
            min_temporal_distance=args.min_distance if args.min_distance is not None else preset_cfg.min_temporal_distance,
            max_temporal_gap=args.max_gap if args.max_gap is not None else preset_cfg.max_temporal_gap,
            dedup_threshold=args.dedup_threshold if args.dedup_threshold is not None else preset_cfg.dedup_threshold,
            scene_threshold=args.scene_threshold if args.scene_threshold is not None else preset_cfg.scene_threshold,
            motion_blur_penalty=args.motion_blur_penalty if args.motion_blur_penalty is not None else preset_cfg.motion_blur_penalty,
            flattery_filter=args.flattery if args.flattery is not None else preset_cfg.flattery_filter,
            action_peak_detection=args.action_peaks if args.action_peaks is not None else preset_cfg.action_peak_detection,
            duplicate_removal=not args.no_dedup if args.no_dedup else preset_cfg.duplicate_removal,
            generate_contact_sheet=not args.no_contact_sheet if args.no_contact_sheet else preset_cfg.generate_contact_sheet,
            scene_detection=not args.no_scene_detection if args.no_scene_detection else preset_cfg.scene_detection,
            adaptive_sampling=not args.no_adaptive_sampling if args.no_adaptive_sampling else preset_cfg.adaptive_sampling,
            quality_scoring=not args.no_quality_scoring if args.no_quality_scoring else preset_cfg.quality_scoring,
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

            workers_count = args.workers or min(os.cpu_count() or 4, max(1, len(video_files)))
            print(f"Found {len(video_files)} video(s). Processing with {workers_count} concurrent worker(s)...")

            from vitupi.pipeline import batch_extract_pipeline

            def on_progress(done, total, path, res):
                photos_count = len(res.photos) if res else 0
                print(f"  [{done}/{total}] Finished: {os.path.basename(path)} ({photos_count} photos)")

            results = batch_extract_pipeline(
                video_files,
                output_base_dir=args.output,
                config=config,
                max_workers=workers_count,
                progress_callback=on_progress,
            )

            total_extracted = sum(len(r.photos) for r in results)
            print(f"\nBatch processing complete. Successfully processed {len(results)}/{len(video_files)} videos ({total_extracted} total photographs extracted).")
            return 0
        else:
            print(f"Input path does not exist: {target}", file=sys.stderr)
            return 1

    elif args.command == "benchmark":
        video_target = args.video
        if not os.path.isfile(video_target):
            print(f"Benchmark video file not found: {video_target}", file=sys.stderr)
            return 1

        from vitupi.benchmark import run_benchmark
        from vitupi.presets import get_preset_manager

        pm = get_preset_manager()
        preset_cfg = pm.get_preset_config(args.preset)
        try:
            domain_preset = DomainPreset(args.preset.lower())
        except ValueError:
            domain_preset = DomainPreset.CUSTOM

        config = VitupiConfig(
            mode=ExtractionMode(args.mode),
            preset=domain_preset,
            custom_name=args.preset if domain_preset == DomainPreset.CUSTOM else None,
            base_fps=preset_cfg.base_fps,
            dense_fps=preset_cfg.dense_fps,
            novelty_threshold=preset_cfg.novelty_threshold,
            min_sharpness_score=preset_cfg.min_sharpness_score,
            dedup_threshold=preset_cfg.dedup_threshold,
        )

        print(f"Running benchmark on: {video_target} (preset: {args.preset}, mode: {args.mode})...")
        report = run_benchmark(video_target, config=config)
        print(report.format_table())

        if args.output_json:
            out_file = report.to_json(args.output_json)
            print(f"\nBenchmark JSON report saved to: {out_file}")

        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
