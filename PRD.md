# Vitupi (V2P)
## Product Requirements Document (PRD)

**Product name:** Vitupi  
**Meaning:** V2P — Video to Photos  
**Product type:** Open-source Python library  
**Primary purpose:** Intelligent, content-aware photograph extraction from videos  
**Target users:** Python developers, photographers, video editors, researchers, archivists, and AI/ML developers  
**Initial platform:** Windows, Linux, and macOS  
**Execution model:** Local processing by default; no cloud dependency  
**Status:** Proposed — Version 0.1 MVP specification

---

# 1. Product Vision

Vitupi is a Python library that transforms videos into collections of meaningful, visually distinct photographs by identifying the most valuable frames in a video.

Unlike conventional frame extractors that capture images at fixed time intervals, Vitupi analyzes the visual content of a video to determine when a new photograph is worth preserving.

Consider a video containing a group of people. The first 200 frames might show nearly identical compositions. Later, the camera pans across the group, reveals new people, changes angles, or cuts to another scene. Those brief transitions may contain more useful photographs than the entire preceding sequence.

Vitupi should recognize this difference.

Its objective is to maximize the number of **useful, distinct photographs** extracted while minimizing redundant images, missed visual moments, and unnecessary computation.

### Core principle

**Extract photographs according to visual significance, not elapsed time.**

Vitupi should be useful as a standalone library, a command-line application, and eventually the processing engine behind graphical video-to-photo tools.

# 2. Problem Statement

Existing frame-extraction workflows generally rely on one or more of these methods:

- Extract a frame every N seconds.
- Extract every Nth frame.
- Extract the first or middle frame of each detected scene.
- Select frames based on image sharpness.
- Extract frames when a basic pixel-difference threshold is exceeded.

Each approach has limitations.

### 2.1 Fixed-interval extraction

A video sampled once per second may miss a character appearing for 300 milliseconds. Conversely, it may produce dozens of nearly identical images during a long, static shot.

### 2.2 Scene-based extraction

Scene-cut detection identifies boundaries between shots but cannot necessarily detect meaningful changes within a continuous shot, such as a camera pan revealing additional people.

### 2.3 Motion-based extraction

Motion is not equivalent to novelty. A moving person, a camera shake, or a small camera adjustment can create substantial frame differences without producing a valuable new photograph.

### 2.4 Sharpness-based extraction

A sharpness-only selector can choose hundreds of crisp but redundant images of the same composition while missing a slightly less sharp frame containing an important new subject.

### 2.5 The underlying problem

Vitupi must distinguish between:

1. **Temporal redundancy:** Different frames that communicate essentially the same visual information.
2. **Visual novelty:** A new person, composition, camera angle, subject arrangement, or scene.
3. **Photographic quality:** Whether a candidate frame is sufficiently sharp, well exposed, and usable.
4. **Coverage:** Whether the final collection represents the meaningful visual moments throughout the video.

These factors must be considered together.

# 3. Product Goals

## 3.1 Primary goals

1. Extract visually distinct photographs from video files automatically.
2. Detect scene cuts and transitions.
3. Detect meaningful visual changes within continuous shots.
4. Preserve brief visual moments without processing every frame with expensive models.
5. Rank candidate images using configurable quality metrics.
6. Remove redundant photographs without eliminating genuinely different compositions.
7. Offer predictable, reproducible extraction settings.
8. Provide a clean, documented Python API.
9. Support batch processing and command-line usage.
10. Operate locally without requiring an internet connection after installation and any optional model setup.

## 3.2 Secondary goals

- Generate contact sheets for reviewing extracted photographs.
- Preserve source timestamps and frame metadata.
- Support optional face-aware selection.
- Allow users to control extraction aggressiveness.
- Support optional semantic image embeddings for more sophisticated novelty detection.
- Provide hooks for future GUI applications and video-processing workflows.

## 3.3 Non-goals for the MVP

The first release will not attempt to:

- Generate new photographs using generative AI.
- Reconstruct missing or obscured image content.
- Perform full object tracking across an entire video.
- Guarantee that every person or object has been recognized.
- Automatically identify the narrative importance of every frame.
- Replace professional photo-editing software.
- Require cloud APIs or paid services.
- Build a complete graphical video editor.

# 4. Target Users and Use Cases

## 4.1 Primary use cases

**A. Extracting photographs from films and clips**

A user wants representative stills from a movie, short film, or recorded scene without manually scrubbing through the entire video.

**B. Group and event photography**

A user records a gathering, event, or group interaction and wants multiple photographs showing different people, expressions, and arrangements.

**C. Extracting images from long recordings**

A user processes lectures, meetings, presentations, or recorded demonstrations where meaningful visual content changes at irregular intervals.

**D. Video dataset preparation**

A developer needs representative frames for computer vision, indexing, annotation, or machine-learning datasets.

**E. Batch video processing**

A user supplies a directory of videos and wants a separate collection of selected photographs for each source video.

**F. Sports and athletic peak-action capture**

An athlete, coach, or creator records continuous high-speed movement (e.g., striking a football, swinging a golf club, gymnast jump apex) and wants the exact millisecond frames showcasing peak athletic form and extension without manual frame-by-frame scrubbing.

**G. Surveillance and forensic CCTV inspection**

An investigator or security team reviews hours of static surveillance footage and needs to automatically extract only the moments where novel movement, persons, or vehicles appeared, preserving strict frame timestamps locally without cloud data transfers.

**H. Aesthetic candid and event portraiture**

A videographer, parent, or content creator transforms spontaneous party, wedding, or candid family video into magazine-quality stills, automatically filtering out unflattering mid-speech mouth shapes or closed eyes (blinks).

# 5. Product Requirements

## P0 — Mandatory MVP features

### 5.1 Video ingestion

Vitupi must:

- Accept common video formats, including MP4, MOV, MKV, AVI, and WebM, subject to codec support.
- Accept individual video paths and batches of files.
- Read frame timestamps and source video metadata.
- Handle variable frame rates where the decoding backend exposes sufficient timestamp information.
- Support configurable output directories.
- Report unsupported codecs, corrupt files, and decoding failures clearly.
- Release decoding resources safely when processing finishes or fails.

The library should use a reliable video-decoding backend, such as PyAV or OpenCV. The initial implementation should select one primary backend and avoid unnecessary duplicate decoding work.

### 5.2 Scene-boundary detection

Vitupi must detect likely transitions between shots.

Supported boundary types should include:

- Hard cuts.
- Fades and gradual transitions where supported.
- Abrupt visual changes.
- Optional detection of unusually long static scenes.

Scene boundaries partition a video into manageable segments for subsequent analysis.

**Proposed implementation:** Integrate PySceneDetect initially, with an abstraction allowing another detector to be substituted later.

Scene boundaries must not automatically determine the number of exported photographs. A single shot may contain several valuable visual moments, and a transition may not always produce a useful standalone frame.

### 5.3 Within-scene visual novelty detection

This is the central Vitupi feature.

The library must evaluate frames within a scene and estimate whether the visual content has changed enough to justify retaining another photograph.

Potential signals include:

- Color histogram differences.
- Perceptual image differences.
- Structural similarity.
- Edge and composition changes.
- Global camera motion.
- Changes in the spatial distribution of image features.
- Optional semantic embedding differences.

The novelty detector should distinguish, as far as practical, between substantial visual changes and insignificant movement.

Examples:

- A small head movement should not automatically create a new photograph.
- A pan revealing an additional person should increase novelty.
- A close-up replacing a wide shot should generally be considered a meaningful change.
- A cut to a different scene should trigger fresh candidate selection.
- Camera shake should not generate dozens of redundant photographs.

No single signal is sufficient for every video. Vitupi should combine several inexpensive signals before invoking optional, more expensive analysis.

### 5.4 Adaptive temporal sampling

Vitupi must avoid processing every frame with every analysis stage.

The initial algorithm should support adaptive sampling:

- Sample relatively sparsely during stable visual periods.
- Increase sampling density when novelty rises.
- Analyze around likely scene boundaries at higher temporal resolution.
- Reduce sampling density once the scene stabilizes.
- Enforce configurable minimum and maximum sampling rates.

The sampling mechanism must account for the source frame rate and actual timestamps rather than assuming every video has a constant frame rate.

The system should preserve the ability to perform a denser second pass around detected events.

**Important:** The system must not rely exclusively on sparse sampling. A very brief appearance could occur between sampled frames. Higher-resolution sampling around likely changes, along with optional exhaustive scanning, should help reduce these misses.

### 5.5 Candidate frame generation

Vitupi should create a candidate set containing frames around meaningful visual changes.

Candidate generation should consider:

- The frame before a transition.
- The frame at or near the transition.
- Frames shortly after the transition.
- Local novelty peaks.
- Potentially important compositions within stable scenes.
- Additional candidates requested by the selected extraction mode.

The library should retain frame timestamps and source frame indices wherever available.

A candidate must not be exported automatically merely because it was generated.

### 5.6 Image-quality scoring

Each candidate must receive a configurable quality score.

The initial quality model should consider:

- Sharpness.
- Motion blur indicators.
- Exposure and clipping.
- Optional contrast and image usability metrics.
- Optional face visibility and facial sharpness.

A Laplacian-variance score may be used as an initial sharpness estimator. It must not be treated as a universal measure of photographic quality.

Quality metrics should be normalized or calibrated sufficiently to prevent one metric's numerical scale from dominating the others unintentionally.

A low-quality candidate may still be retained if it contains an otherwise unique visual moment and the user's settings permit it.

### 5.7 Near-duplicate suppression

Vitupi must identify and suppress redundant candidates.

Initial techniques should include perceptual hashing and image similarity comparisons.

The algorithm should distinguish between:

- Nearly identical frames.
- Similar frames with slightly different expressions.
- Different camera angles of the same subject.
- Different subject arrangements.
- Meaningfully different photographs within the same scene.

Deduplication should operate on candidates, not merely adjacent source frames. Two similar photographs may be separated by several seconds and still be redundant.

The deduplication threshold must be configurable.

The library should not assume that a single universal threshold works equally well for all videos.

### 5.8 Final photograph selection

Vitupi must select a final collection balancing:

- Visual novelty.
- Image quality.
- Coverage across scenes.
- Temporal distribution.
- Redundancy suppression.
- User-configured output limits.

The selector should use a diversity-aware strategy, such as greedy selection based on novelty and quality, with a temporal coverage mechanism to avoid neglecting long or visually diverse scenes.

The final collection must not simply consist of the globally sharpest frames.

### 5.9 Output and metadata

The library must export selected images in a configurable format, with JPEG and PNG supported in the initial release.

For each exported photograph, Vitupi should preserve:

- Output filename.
- Source video.
- Source timestamp.
- Source frame index, when available.
- Image dimensions.
- Quality score.
- Novelty score.
- Scene identifier.
- Selection reason or relevant metadata.

The library should also support a machine-readable JSON report.

A future release may support CSV metadata and additional image formats.

## P1 — High-priority enhancements

- Face-aware frame selection and flattery filtering (eye-blink rejection, smile/expression scoring).
- Motion inflection and action-peak detection for sports and athletic analysis.
- Domain-specific extraction presets (`sports`, `security`, `candid`).
- Semantic embedding-based novelty detection.
- Optional local AI models.
- Contact sheet generation.
- More sophisticated camera-motion analysis.
- Scene-specific extraction limits.
- Batch processing with parallelism.
- Checkpointing and resumable processing.
- Progress callbacks.
- User-supplied scoring functions.
- Custom novelty detectors and selection strategies.

## P2 — Future features

- A graphical review interface.
- Interactive threshold tuning.
- Video timeline visualization.
- Person-aware diversity selection.
- Scene and subject clustering.
- Video indexing and searchable image collections.
- Plugin architecture for additional computer vision models.
- GPU acceleration where supported.
- Optional image similarity search across multiple videos.

# 6. Extraction Modes

Vitupi should expose three primary modes.

## 6.1 Conservative mode

Purpose: Generate a small collection of high-quality, representative photographs.

Characteristics:

- Aggressive duplicate suppression.
- Higher novelty requirements.
- Strong preference for image quality.
- Lower output count.

Suitable for: Quick summaries, representative stills, and small image collections.

## 6.2 Balanced mode

Purpose: Preserve meaningful visual variety without excessive redundancy.

Characteristics:

- Moderate novelty requirements.
- Balanced quality and diversity scoring.
- Multiple photographs from visually diverse scenes.
- Adaptive sampling around transitions.

This should be the default mode.

## 6.3 Exhaustive mode

Purpose: Preserve as many meaningfully distinct visual moments as practical.

Characteristics:

- Lower novelty thresholds.
- Denser temporal sampling.
- Less aggressive deduplication.
- Greater sensitivity to short-lived compositions and appearances.

Suitable for: Dataset creation, detailed scene analysis, and users willing to review more photographs.

Exhaustive mode should still suppress exact or near-exact duplicates according to the user's configuration.

## 6.4 Domain Presets

In addition to density modes, Vitupi provides domain-tailored extraction profiles:

1. **`--preset sports` (Action & Kinematics)**
   - Prioritizes motion inflection points (e.g. acceleration zero-crossings, jump peaks).
   - Higher shutter-speed preference and reduced blur tolerance.
   - Denser temporal bursts around detected high-velocity action.

2. **`--preset security` (CCTV & Surveillance)**
   - Ultra-aggressive static background suppression (skips 99%+ of identical surveillance footage).
   - Preserves strict timestamp audit logs for chain of custody.
   - Heightened sensitivity to localized region-of-interest (ROI) visual changes.

3. **`--preset candid` (Social, Events & Portraits)**
   - Incorporates facial flattery heuristics: filters out blinking/closed eyes and mid-sentence mouth contortions.
   - Balances subject sharpness with composition and natural expression.

# 7. Proposed Algorithm

The MVP should use a modular, multi-stage pipeline rather than a single opaque score.

## Stage 1: Inspect the video

Read video metadata, timestamps, frame dimensions, duration, and decoding information.

## Stage 2: Detect scene boundaries

Run the scene detector to partition the video into shots or segments.

## Stage 3: Perform coarse analysis

Sample frames at a configurable rate and calculate inexpensive visual signals.

For example:

- Histogram distance.
- Perceptual differences.
- Basic sharpness estimates.
- Edge distribution changes.

## Stage 4: Detect potential novelty events

Combine visual signals into a novelty score.

When the score increases sharply, schedule denser sampling around the event.

## Stage 5: Generate candidates

Collect representative frames from each event window and from sufficiently diverse portions of the scene.

## Stage 6: Evaluate candidates

Calculate quality scores and, where enabled, semantic or face-aware scores.

## Stage 7: Suppress redundant images

Compare candidates and remove redundant alternatives while preserving meaningful compositional differences.

## Stage 8: Select a diverse final collection

Choose candidates that maximize overall quality and visual coverage, subject to the configured extraction mode and output constraints.

## Stage 9: Export results

Save images, timestamps, metadata, and an optional contact sheet.

## 7.1 Proposed selection objective

The final selector should conceptually optimize:

**Total utility = visual novelty + photographic quality + coverage − redundancy**

This is a conceptual objective, not a final mathematical formula. The implementation should normalize its component scores and tune their weights through experiments.

The algorithm should also use explicit constraints where useful, such as a minimum temporal separation, a per-scene output limit, or a maximum total image count.

These constraints must remain configurable because a brief, visually rich scene may legitimately deserve several photographs in quick succession.

## 7.2 Camera-motion handling

Camera movement requires special treatment.

A large frame difference can occur because:

- The camera pans or tilts.
- The camera zooms.
- The camera shakes.
- A new person enters the shot.
- The composition changes meaningfully.

Vitupi should initially use inexpensive image-level signals, then introduce global-motion estimation when needed.

Optical flow or feature-based motion estimation may help characterize camera movement. However, global motion alone cannot determine whether a newly revealed person is important. The novelty detector must also evaluate the resulting image content.

Semantic embeddings should remain an optional enhancement rather than an MVP dependency.

# 8. Python API Design

The library should expose a small public API and hide internal pipeline complexity behind stable interfaces.

The following is a proposed interface, not an existing implementation.

## 8.1 Basic usage

```python
from vitupi import extract_photos

result = extract_photos(
    "video.mp4",
    output_dir="photos/",
)

print(f"Extracted {len(result.photos)} photos")

for photo in result.photos:
    print(photo.path, photo.timestamp)
```

## 8.2 Configurable extraction

```python
from vitupi import extract_photos

result = extract_photos(
    "video.mp4",
    output_dir="photos/",
    mode="balanced",
    preserve_scene_changes=True,
    remove_duplicates=True,
    prefer_sharp_frames=True,
    max_photos=100,
)
```

## 8.3 Custom configuration

```python
from vitupi import VitupiConfig, extract_photos

config = VitupiConfig(
    mode="balanced",
    scene_detection=True,
    adaptive_sampling=True,
    duplicate_removal=True,
    quality_scoring=True,
    max_photos=100,
)

result = extract_photos(
    "video.mp4",
    output_dir="photos/",
    config=config,
)
```

## 8.4 Result structure

The result object should expose:

- `photos`: Selected photo records.
- `timestamps`: Source timestamps of selected images.
- `source_video`: Input path or source identifier.
- `metadata`: Video and extraction metadata.
- `statistics`: Candidate counts, rejection counts, and processing statistics.
- `report_path`: Path to the optional JSON report.

Each photo record should expose its image path, timestamp, scene identifier, frame index when available, quality score, and novelty score.

The API should remain consistent across extraction modes.

# 9. Command-Line Interface

Vitupi should provide a CLI for users who do not want to write Python code.

Example:

```bash
vitupi extract video.mp4 --output photos/
```

Configurable options should include:

```bash
vitupi extract video.mp4 \
    --output photos/ \
    --mode balanced \
    --max-photos 100 \
    --deduplicate \
    --contact-sheet
```

The CLI should support:

- Single-video extraction.
- Batch directory processing.
- Output-directory selection.
- Extraction mode selection.
- Maximum output count.
- Deduplication settings.
- Quality and novelty thresholds.
- Contact sheet generation.
- JSON reporting.
- Verbose logging.
- Progress reporting.
- Exit codes suitable for scripting.

Exact option names may change during implementation, but the interface should remain coherent and documented.

# 10. Architecture

Vitupi should be designed as a modular library.

Proposed package structure:

```text
vitupi/
├── __init__.py
├── api.py
├── config.py
├── models.py
├── exceptions.py
├── pipeline.py
├── video/
│   ├── decoder.py
│   └── metadata.py
├── detection/
│   ├── scenes.py
│   ├── novelty.py
│   └── motion.py
├── sampling/
│   ├── adaptive.py
│   └── candidates.py
├── scoring/
│   ├── sharpness.py
│   ├── exposure.py
│   └── composite.py
├── deduplication/
│   ├── hashing.py
│   └── similarity.py
├── selection/
│   ├── diversity.py
│   └── ranking.py
├── export/
│   ├── images.py
│   ├── metadata.py
│   └── contact_sheet.py
└── cli.py
```

Tests and documentation should live in separate top-level directories.

### Architectural requirements

- Each major pipeline stage should be independently testable.
- Internal components should communicate through clearly defined data structures.
- The public API should not expose implementation-specific objects unnecessarily.
- Expensive optional features should not be imported unless required.
- Video decoding should not be repeated unnecessarily.
- Configuration should be explicit and validated.
- Failures should produce actionable error messages.
- Optional model dependencies should not be required for basic operation.

# 11. Technology Stack

| Component | Proposed technology |
|---|---|
| Language | Python |
| Video decoding | PyAV or OpenCV |
| Scene detection | PySceneDetect |
| Numerical processing | NumPy |
| Image processing | OpenCV |
| Image quality and similarity | OpenCV and scikit-image |
| Perceptual hashing | OpenCV image hashing or a suitable hashing package |
| Image export | Pillow |
| Optional semantic embeddings | A locally runnable CLIP/SigLIP-compatible implementation |
| Testing | pytest |
| Packaging | pyproject.toml and a modern Python build backend |
| Documentation | Markdown with a documentation site in a later release |
| Continuous integration | GitHub Actions |

The initial release should minimize mandatory dependencies. The exact minimum Python version should be selected after checking compatibility across the chosen dependencies.

# 12. Performance and Resource Requirements

Vitupi should be designed for ordinary desktop computers, including systems without dedicated GPUs.

Requirements:

- Basic extraction must work on a CPU.
- GPU acceleration must not be mandatory.
- Memory usage should remain bounded for long videos.
- Frames should be decoded and processed incrementally rather than loading entire videos into memory.
- Optional AI analysis should be independently configurable.
- Processing should avoid unnecessary repeated decoding.
- The library should provide progress and timing statistics.
- Batch processing should allow users to limit concurrency.
- Large output collections should not require all images to remain in memory.

The project should establish actual speed benchmarks before promising a specific processing speed.

# 13. Output Organization

A default extraction directory could look like this:

```text
photos/
├── frame_000001_00-00-01-240.jpg
├── frame_000002_00-00-03-680.jpg
├── frame_000003_00-00-04-120.jpg
├── frame_000004_00-00-12-400.jpg
├── contact_sheet.jpg
└── vitupi_report.json
```

Filenames should contain a stable sequence number and a human-readable timestamp. The exact timestamp format should be documented.

The JSON report should include the input video, configuration, extraction statistics, and a record for each selected photograph.

If processing fails partway through, Vitupi should avoid presenting an incomplete collection as a fully successful run. It should clearly report partial results when recovery is possible.

# 14. Error Handling and Reliability

Vitupi must handle:

- Missing input files.
- Unsupported formats and codecs.
- Corrupt or truncated video files.
- Videos with unusual timestamps.
- Empty or very short videos.
- Videos with no detected scene cuts.
- Insufficient storage space.
- Invalid configuration values.
- Optional dependency failures.
- Interruption during processing.

The library should distinguish between fatal errors and recoverable warnings.

For batch processing, one failed video should not necessarily terminate processing of every other input file.

# 15. Testing Strategy

Testing must evaluate the actual usefulness of the extracted collection, not merely whether image files were produced.

## 15.1 Unit tests

Test:

- Scene-boundary processing.
- Novelty-score calculations.
- Sharpness and exposure metrics.
- Duplicate suppression.
- Selection constraints.
- Timestamp handling.
- Metadata serialization.
- Configuration validation.

## 15.2 Synthetic video tests

Create controlled videos containing:

1. A long static shot.
2. Small movements within a stable composition.
3. A camera pan revealing a new person.
4. A close-up replacing a wide shot.
5. A hard cut between unrelated scenes.
6. A gradual fade.
7. A brief visual event.
8. Camera shake without a meaningful scene change.
9. Repeated shots at different timestamps.
10. Blurry and well-focused alternatives.
11. A variable-frame-rate video, where test fixtures permit.
12. A mixture of stable scenes and rapid cuts.

Synthetic tests should make it possible to know which frames or events the system ought to preserve.

## 15.3 Real-world evaluation

Build a small, diverse benchmark of publicly usable or appropriately licensed videos.

Include human-reviewed reference selections to measure:

- Important visual events preserved.
- Redundant images retained.
- Unique events missed.
- Overall visual diversity.
- Photographic usability.
- Processing time.

The benchmark should contain difficult cases, not only videos that make the algorithm look good.

# 16. Acceptance Criteria

The MVP will be considered ready when all of the following are satisfied.

1. A user can install Vitupi and extract photographs from a supported video using the Python API.
2. The CLI can process an individual video and a directory of videos.
3. Scene boundaries and within-scene novelty are evaluated independently.
4. A stable shot does not generate excessive redundant output under balanced settings.
5. A camera pan revealing a new person can produce additional selected photographs without requiring a hard cut.
6. Abrupt scene changes trigger fresh candidate selection.
7. Candidate selection considers image quality and redundancy.
8. A short visual event can be preserved when it falls within the system's sampling resolution.
9. Selected images have traceable timestamps and metadata.
10. Processing does not require the entire video to be held in memory.
11. Core functionality runs without a GPU or a remote service.
12. Tests cover the principal synthetic scenarios.
13. Installation instructions, API documentation, and known limitations are published.
14. The project reports meaningful benchmark results rather than claiming universal accuracy.

The benchmark should establish numerical targets for duplicate suppression, event coverage, and processing performance after the first prototype has been evaluated.

# 17. Development Roadmap

## Phase 1 — Functional foundation

- Create the package structure.
- Implement video decoding and metadata handling.
- Integrate scene detection.
- Implement frame sampling.
- Export basic representative frames.
- Add initial tests and documentation.

**Deliverable:** A working video-to-keyframes library.

## Phase 2 — Intelligent selection

- Implement visual novelty scoring.
- Add adaptive sampling.
- Implement sharpness and exposure scoring.
- Add perceptual duplicate suppression.
- Introduce balanced, conservative, and exhaustive modes.

**Deliverable:** A functional content-aware photo extractor.

## Phase 3 — Diversity and quality

- Improve selection across scenes.
- Add event-window analysis.
- Introduce a configurable diversity-aware selector.
- Add contact sheets and JSON reports.
- Benchmark against synthetic and real-world videos.

**Deliverable:** A useful beta suitable for external testing.

## Phase 4 — Advanced intelligence

- Add optional semantic embeddings.
- Improve camera-motion analysis.
- Add optional face-aware selection.
- Expose plugin interfaces for custom detectors and scorers.
- Optimize CPU performance and memory use.

**Deliverable:** An extensible, more sophisticated extraction engine.

## Phase 5 — Public release

- Finalize the API.
- Complete installation and compatibility testing.
- Publish documentation.
- Configure continuous integration.
- Publish a versioned release on GitHub and PyPI.
- Collect feedback and prioritize fixes.

**Deliverable:** Vitupi 1.0, subject to release-readiness criteria.

# 18. Risks and Mitigations

**Risk: Camera motion produces too many candidates.**

Mitigation: Combine global-motion analysis with content novelty, candidate-window consolidation, and deduplication.

**Risk: Important short-lived appearances are missed.**

Mitigation: Adaptive temporal sampling, denser analysis around transitions, and an exhaustive mode. Document that events shorter than the effective sampling interval can still be missed.

**Risk: Duplicate suppression removes meaningful expressions or angles.**

Mitigation: Use configurable thresholds, compare more than one similarity signal, and evaluate duplicate suppression against human-reviewed examples.

**Risk: Semantic models make installation and execution expensive.**

Mitigation: Keep semantic analysis optional and make the conventional computer-vision pipeline fully functional on its own.

**Risk: Too many configuration parameters make the library difficult to use.**

Mitigation: Offer sensible defaults and three high-level modes, with advanced settings available when needed.

**Risk: Different types of video require different selection strategies.**

Mitigation: Use configurable scoring, establish representative benchmarks, and avoid hardcoding assumptions about one genre or recording style.

# 19. Success Metrics

Vitupi's success should be measured through a combination of technical and user-oriented metrics.

- **Visual-event recall:** Fraction of human-identified important moments represented in the output.
- **Redundancy rate:** Fraction of selected images considered unnecessarily similar.
- **Photographic usability:** Fraction of exported images judged usable by human reviewers.
- **Scene coverage:** Proportion of relevant scenes represented.
- **Brief-event retention:** Success rate for detecting short-lived visual moments in controlled tests.
- **Processing efficiency:** Time and memory consumed per minute of input video.
- **API usability:** Whether a new user can perform basic extraction with a short Python script.
- **Reliability:** Successful processing rate across supported inputs.

Targets should be established using the benchmark dataset rather than selected arbitrarily.

# 20. Distribution and Licensing

Vitupi should be developed as an open-source Python project with:

- A public GitHub repository.
- Versioned releases.
- A PyPI package.
- Installation and usage documentation.
- A changelog and contribution guide.
- Automated testing for supported Python versions and operating systems.
- A clear open-source license.

The project should select its license after reviewing the licenses of required dependencies and optional integrations. Third-party model weights and codecs may have separate licensing conditions.

# 21. Final Product Definition

Vitupi is not simply a tool that converts videos into images. It is a configurable engine for identifying and preserving the most useful visual moments in a video.

Its defining capability is the combination of scene-boundary detection, adaptive temporal sampling, visual novelty analysis, photographic quality scoring, and diversity-aware selection.

The first priority is not to build the most complicated AI pipeline possible. It is to build a dependable baseline that selects better photographs than fixed-interval extraction, measure where it fails, and improve the algorithm incrementally.

**Vitupi — Video to Photos. More visual moments, fewer redundant frames.**