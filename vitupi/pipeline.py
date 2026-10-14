"""
Master processing pipeline coordinating all extraction stages.
"""

import os
import time
from typing import Any, Callable, Dict, List, Optional
from vitupi.config import VitupiConfig
from vitupi.deduplication.similarity import suppress_near_duplicates
from vitupi.detection.motion import MotionAnalyzer
from vitupi.detection.novelty import VisualNoveltyDetector
from vitupi.detection.scenes import detect_scenes
from vitupi.exceptions import VideoDecodingError
from vitupi.export.contact_sheet import generate_contact_sheet
from vitupi.export.images import export_photos
from vitupi.export.metadata import export_json_report
from vitupi.models import ExtractionResult, ExtractionStatistics
from vitupi.sampling.adaptive import AdaptiveSampler
from vitupi.sampling.candidates import CandidateGenerator
from vitupi.scoring.composite import score_candidate
from vitupi.selection.diversity import select_diverse_photos
from vitupi.video.decoder import VideoDecoder
from vitupi.video.metadata import extract_metadata


class ExtractionPipeline:
    """End-to-end video-to-photograph processing pipeline."""

    def __init__(self, config: Optional[VitupiConfig] = None):
        self.config = config or VitupiConfig()

    def process(self, video_path: str, output_dir: str = "photos/") -> ExtractionResult:
        """Run the complete extraction workflow on the target video.

        Args:
            video_path: Absolute or relative path to the video file.
            output_dir: Directory where selected photographs will be saved.

        Returns:
            ExtractionResult containing all photos, metadata, and statistics.
        """
        start_time = time.time()
        stats = ExtractionStatistics()

        # Stage 1: Inspect video metadata
        metadata = extract_metadata(video_path)
        stats.total_frames_in_video = metadata.total_frames

        # Stage 2: Detect scene boundaries
        if self.config.scene_detection:
            scenes = detect_scenes(video_path, metadata, threshold=self.config.scene_threshold)
        else:
            scenes = [detect_scenes(video_path, metadata, threshold=999.0)[0]]
        stats.scenes_detected = len(scenes)

        # Stage 3-5: Adaptive sampling, novelty evaluation, and candidate generation
        novelty_detector = VisualNoveltyDetector()
        motion_analyzer = MotionAnalyzer()
        sampler = AdaptiveSampler(
            base_fps=self.config.base_fps,
            dense_fps=self.config.dense_fps,
        )
        candidate_gen = CandidateGenerator(
            novelty_threshold=self.config.novelty_threshold,
            min_temporal_distance=self.config.min_temporal_distance,
            max_temporal_gap=self.config.max_temporal_gap,
        )

        current_scene_idx = 0
        current_scene = scenes[current_scene_idx]

        with VideoDecoder(video_path) as decoder:
            # Stream sampled frames sequentially
            # We sample at maximum potential resolution, and let sampler filter adaptively
            scan_fps = max(self.config.dense_fps, self.config.base_fps)
            for frame_idx, timestamp_sec, frame in decoder.stream_sampled_frames(scan_fps):
                stats.frames_decoded += 1

                # Update current scene
                if current_scene_idx + 1 < len(scenes):
                    if timestamp_sec >= scenes[current_scene_idx + 1].start_time_sec:
                        current_scene_idx += 1
                        current_scene = scenes[current_scene_idx]
                        novelty_detector.reset_anchor()
                        motion_analyzer.reset()
                        if self.config.adaptive_sampling:
                            sampler.trigger_burst(timestamp_sec)

                # Check sampling gate
                if not sampler.should_sample_frame(frame_idx, metadata.fps, timestamp_sec):
                    continue

                if self.config.adaptive_sampling:
                    # Motion and action inflection analysis
                    _, is_action_peak = motion_analyzer.analyze_frame(frame)
                    if self.config.action_peak_detection and is_action_peak:
                        sampler.trigger_burst(timestamp_sec)

                    # Novelty analysis
                    novelty = novelty_detector.compute_novelty(frame)

                    # If significant novelty detected, trigger a burst window
                    if novelty >= self.config.novelty_threshold:
                        sampler.trigger_burst(timestamp_sec)
                else:
                    novelty = 0.0
                    is_action_peak = False

                # Force candidate if action peak or scene boundary
                is_boundary = (frame_idx == current_scene.start_frame)
                force = is_boundary or (self.config.action_peak_detection and is_action_peak)

                cand = candidate_gen.evaluate_and_add(
                    frame_idx=frame_idx,
                    timestamp_sec=timestamp_sec,
                    scene_id=current_scene.scene_id,
                    frame=frame,
                    novelty_score=novelty,
                    force_candidate=force,
                )

                if cand is not None:
                    # Update anchor for subsequent cumulative novelty
                    novelty_detector.set_anchor(frame)

        candidates = candidate_gen.candidates
        stats.candidates_generated = len(candidates)

        # Stage 6: Quality scoring and sharpness filtering
        active_candidates = []
        for cand in candidates:
            if self.config.quality_scoring:
                score_candidate(cand, self.config)
            else:
                cand.quality_score = 1.0
                cand.is_rejected = False

            if cand.is_rejected:
                stats.low_quality_filtered += 1
            else:
                active_candidates.append(cand)

        # Stage 7: Near-duplicate suppression
        if self.config.duplicate_removal and len(active_candidates) > 1:
            active_candidates, dups_count = suppress_near_duplicates(
                active_candidates,
                threshold=self.config.dedup_threshold,
            )
            stats.duplicates_suppressed = dups_count

        # Stage 8: Diversity-aware final selection
        selected_candidates = select_diverse_photos(
            active_candidates,
            max_photos=self.config.max_photos,
            min_temporal_distance=self.config.min_temporal_distance,
        )

        # Stage 9: Export photos, JSON report, and contact sheet
        exported_photos = export_photos(selected_candidates, output_dir=output_dir)
        stats.photos_exported = len(exported_photos)
        stats.processing_time_sec = time.time() - start_time

        result = ExtractionResult(
            source_video=video_path,
            photos=exported_photos,
            metadata=metadata,
            statistics=stats,
        )

        if self.config.generate_json_report:
            export_json_report(result, output_dir=output_dir)

        if self.config.generate_contact_sheet and exported_photos:
            cs_path = generate_contact_sheet(exported_photos, output_dir=output_dir)
            result.contact_sheet_path = cs_path

        return result

    # Alias for pipeline execution
    run = process


def batch_extract_pipeline(
    video_paths: List[str],
    output_base_dir: str,
    config: VitupiConfig,
    max_workers: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, str, Optional[ExtractionResult]], None]] = None,
) -> List[ExtractionResult]:
    """Execute photo extraction concurrently across multiple video files."""
    import concurrent.futures

    results = []
    total = len(video_paths)
    workers = max_workers or min(os.cpu_count() or 4, max(1, total))

    def _process_one(idx: int, path: str):
        sub_dir = os.path.join(output_base_dir, os.path.splitext(os.path.basename(path))[0])
        pipeline = ExtractionPipeline(config=config)
        res = pipeline.run(path, output_dir=sub_dir)
        if progress_callback:
            progress_callback(idx + 1, total, path, res)
        return res

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_process_one, i, path): path for i, path in enumerate(video_paths)}
        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result()
                results.append(res)
            except Exception:
                continue

    return results
