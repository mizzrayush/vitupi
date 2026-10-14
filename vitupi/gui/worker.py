"""
Background extraction worker thread using PyQt6.
"""

import traceback
from PyQt6.QtCore import QThread, pyqtSignal

from vitupi.config import VitupiConfig
from vitupi.models import ExtractionResult
from vitupi.pipeline import ExtractionPipeline


class ExtractionWorker(QThread):
    """Background worker executing extraction pipeline without blocking the GUI."""

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)  # ExtractionResult
    error = pyqtSignal(str)

    def __init__(self, video_path: str, output_dir: str, config: VitupiConfig):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.config = config
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            self.progress.emit(10, "Inspecting video stream and metadata...")
            pipeline = ExtractionPipeline(config=self.config)

            self.progress.emit(30, "Detecting scene cuts and within-scene visual novelty...")
            result = pipeline.process(video_path=self.video_path, output_dir=self.output_dir)

            self.progress.emit(90, "Finalizing duplicate suppression and export...")
            self.progress.emit(100, f"Extraction complete: {len(result.photos)} photographs selected.")
            self.finished.emit(result)
        except Exception as e:
            traceback.print_exc()
            self.error.emit(str(e))
