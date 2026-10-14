"""
Batch Video Processing Queue Dialog for Vitupi GUI.
Supports multi-video concurrent extraction, worker threading, queue management, and live status.
"""

import os
from typing import List, Optional
from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from vitupi.config import DomainPreset, VitupiConfig
from vitupi.gui.icons import get_svg_icon
from vitupi.models import ExtractionResult
from vitupi.pipeline import batch_extract_pipeline
from vitupi.presets import get_preset_manager


class BatchExtractionWorker(QThread):
    """Worker thread running concurrent video extractions."""

    item_started = pyqtSignal(int, str)       # index, video_path
    item_finished = pyqtSignal(int, str, object)  # index, video_path, ExtractionResult
    batch_finished = pyqtSignal(list)         # list of ExtractionResult
    progress_updated = pyqtSignal(int, int)   # done, total

    def __init__(self, video_paths: List[str], output_base: str, config: VitupiConfig, workers: int):
        super().__init__()
        self.video_paths = video_paths
        self.output_base = output_base
        self.config = config
        self.workers = workers
        self._is_cancelled = False

    def run(self):
        total = len(self.video_paths)
        results = []

        def _on_progress(done_count, total_count, path, res):
            # Find item index
            try:
                idx = self.video_paths.index(path)
            except ValueError:
                idx = done_count - 1
            self.item_finished.emit(idx, path, res)
            self.progress_updated.emit(done_count, total_count)

        # Run pipeline
        results = batch_extract_pipeline(
            self.video_paths,
            output_base_dir=self.output_base,
            config=self.config,
            max_workers=self.workers,
            progress_callback=_on_progress,
        )
        self.batch_finished.emit(results)


class BatchQueueDialog(QDialog):
    """Dialog for managing and executing batch video photo extraction jobs."""

    batch_completed = pyqtSignal(list)

    def __init__(self, parent: Optional[QWidget] = None, initial_preset: str = "default"):
        super().__init__(parent)
        self.setWindowTitle("Batch Processing Queue - Vitupi")
        self.resize(860, 560)
        self.setMinimumSize(700, 450)

        self._video_paths: List[str] = []
        self._worker_thread: Optional[BatchExtractionWorker] = None
        self._initial_preset = initial_preset

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 1. Top Action Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.btn_add_files = QPushButton("Add Videos...")
        self.btn_add_files.setIcon(get_svg_icon("plus", size=16, color="#00E5FF"))
        self.btn_add_files.clicked.connect(self._on_add_files)
        toolbar.addWidget(self.btn_add_files)

        self.btn_add_dir = QPushButton("Add Folder...")
        self.btn_add_dir.setIcon(get_svg_icon("folder", size=16, color="#63B3ED"))
        self.btn_add_dir.clicked.connect(self._on_add_directory)
        toolbar.addWidget(self.btn_add_dir)

        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.setIcon(get_svg_icon("minus", size=16, color="#F56565"))
        self.btn_remove.clicked.connect(self._on_remove_selected)
        toolbar.addWidget(self.btn_remove)

        self.btn_clear = QPushButton("Clear Queue")
        self.btn_clear.setIcon(get_svg_icon("trash", size=16, color="#A0AEC0"))
        self.btn_clear.clicked.connect(self._on_clear_queue)
        toolbar.addWidget(self.btn_clear)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 2. Queue Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Video File", "File Size", "Status", "Source Path"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(0, 220)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(1, 100)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(2, 160)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setStyleSheet(
            "QTableWidget { background-color: #16181E; gridline-color: #2D3748; color: #E2E8F0; }"
            "QHeaderView::section { background-color: #1F2430; color: #A0AEC0; font-weight: bold; padding: 6px; border: 1px solid #2D3748; }"
        )
        layout.addWidget(self.table, 1)

        # 3. Settings Box (Workers, Output Dir, Preset)
        settings_group = QGroupBox("Batch Job Settings")
        settings_group.setStyleSheet("QGroupBox { color: #A0AEC0; font-weight: bold; border: 1px solid #2D3748; margin-top: 8px; padding-top: 12px; }")
        settings_layout = QHBoxLayout(settings_group)

        # Workers
        lbl_workers = QLabel("Concurrent Workers:")
        self.spin_workers = QSpinBox()
        self.spin_workers.setRange(1, 16)
        default_workers = min(8, max(1, os.cpu_count() or 4))
        self.spin_workers.setValue(default_workers)
        settings_layout.addWidget(lbl_workers)
        settings_layout.addWidget(self.spin_workers)

        settings_layout.addSpacing(16)

        # Output folder
        lbl_out = QLabel("Output Base Dir:")
        self.edit_output = QLineEdit(os.path.abspath("photos_batch"))
        self.btn_browse_out = QPushButton("Browse...")
        self.btn_browse_out.clicked.connect(self._on_browse_output)
        settings_layout.addWidget(lbl_out)
        settings_layout.addWidget(self.edit_output, 1)
        settings_layout.addWidget(self.btn_browse_out)

        layout.addWidget(settings_group)

        # 4. Progress bar & status
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #16181E; border: 1px solid #2D3748; border-radius: 4px; text-align: center; color: #FFF; }"
            "QProgressBar::chunk { background-color: #00E5FF; border-radius: 3px; }"
        )
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Ready. Add video files to begin batch extraction.")
        self.lbl_status.setStyleSheet("color: #718096; font-size: 11px;")
        layout.addWidget(self.lbl_status)

        # 5. Bottom Dialog Buttons
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        self.btn_start = QPushButton("Start Batch Extraction")
        self.btn_start.setIcon(get_svg_icon("play", size=16, color="#111827"))
        self.btn_start.setStyleSheet("QPushButton { background-color: #00E5FF; color: #111827; font-weight: bold; padding: 8px 18px; border-radius: 4px; }")
        self.btn_start.clicked.connect(self._on_start_batch)
        bottom_bar.addWidget(self.btn_start)

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(self.btn_close)

        layout.addLayout(bottom_bar)

    def _on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Videos for Batch Processing",
            "",
            "Video Files (*.mp4 *.mov *.mkv *.avi *.webm *.m4v);;All Files (*)",
        )
        for f in files:
            self._add_video_to_queue(f)

    def _on_add_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory Containing Videos")
        if not folder:
            return
        video_exts = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
        for fname in sorted(os.listdir(folder)):
            if os.path.splitext(fname)[1].lower() in video_exts:
                self._add_video_to_queue(os.path.join(folder, fname))

    def _add_video_to_queue(self, path: str):
        if path in self._video_paths:
            return
        self._video_paths.append(path)

        row = self.table.rowCount()
        self.table.insertRow(row)

        name_item = QTableWidgetItem(os.path.basename(path))
        try:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB"
        except Exception:
            size_str = "Unknown"

        size_item = QTableWidgetItem(size_str)
        status_item = QTableWidgetItem("Queued")
        path_item = QTableWidgetItem(path)

        self.table.setItem(row, 0, name_item)
        self.table.setItem(row, 1, size_item)
        self.table.setItem(row, 2, status_item)
        self.table.setItem(row, 3, path_item)

        self.lbl_status.setText(f"{len(self._video_paths)} video(s) queued.")

    def _on_remove_selected(self):
        selected_rows = sorted(set(idx.row() for idx in self.table.selectedIndexes()), reverse=True)
        for row in selected_rows:
            if row < len(self._video_paths):
                del self._video_paths[row]
            self.table.removeRow(row)
        self.lbl_status.setText(f"{len(self._video_paths)} video(s) queued.")

    def _on_clear_queue(self):
        self._video_paths.clear()
        self.table.setRowCount(0)
        self.lbl_status.setText("Queue cleared.")

    def _on_browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Batch Output Directory")
        if folder:
            self.edit_output.setText(folder)

    def _on_start_batch(self):
        if not self._video_paths:
            QMessageBox.information(self, "Batch Queue Empty", "Please add at least one video to the queue.")
            return

        out_base = self.edit_output.text().strip()
        if not out_base:
            out_base = os.path.abspath("photos_batch")

        workers = self.spin_workers.value()

        # Build config from preset
        pm = get_preset_manager()
        preset_cfg = pm.get_preset_config(self._initial_preset)
        try:
            domain_preset = DomainPreset(self._initial_preset.lower())
        except ValueError:
            domain_preset = DomainPreset.CUSTOM

        config = VitupiConfig(
            preset=domain_preset,
            custom_name=self._initial_preset if domain_preset == DomainPreset.CUSTOM else None,
            base_fps=preset_cfg.base_fps,
            dense_fps=preset_cfg.dense_fps,
            novelty_threshold=preset_cfg.novelty_threshold,
            min_sharpness_score=preset_cfg.min_sharpness_score,
            dedup_threshold=preset_cfg.dedup_threshold,
        )

        # Set all table rows to "Processing..."
        for r in range(self.table.rowCount()):
            self.table.item(r, 2).setText("In Progress...")

        self.btn_start.setEnabled(False)
        self.btn_add_files.setEnabled(False)
        self.btn_add_dir.setEnabled(False)
        self.btn_remove.setEnabled(False)
        self.btn_clear.setEnabled(False)

        self.progress_bar.setValue(0)
        self.lbl_status.setText(f"Processing {len(self._video_paths)} videos concurrently across {workers} workers...")

        self._worker_thread = BatchExtractionWorker(
            video_paths=list(self._video_paths),
            output_base=out_base,
            config=config,
            workers=workers,
        )
        self._worker_thread.item_finished.connect(self._on_item_finished)
        self._worker_thread.progress_updated.connect(self._on_progress_updated)
        self._worker_thread.batch_finished.connect(self._on_batch_finished)
        self._worker_thread.start()

    def _on_item_finished(self, idx: int, path: str, res: Optional[ExtractionResult]):
        if 0 <= idx < self.table.rowCount():
            if res and res.photos:
                status = f"Completed ({len(res.photos)} photos)"
            elif res:
                status = "Finished (0 photos)"
            else:
                status = "Failed"
            self.table.item(idx, 2).setText(status)

    def _on_progress_updated(self, done: int, total: int):
        pct = int((done / max(1, total)) * 100)
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(f"Completed {done}/{total} videos ({pct}%)")

    def _on_batch_finished(self, results: list):
        self.btn_start.setEnabled(True)
        self.btn_add_files.setEnabled(True)
        self.btn_add_dir.setEnabled(True)
        self.btn_remove.setEnabled(True)
        self.btn_clear.setEnabled(True)

        total_photos = sum(len(r.photos) for r in results if r)
        self.lbl_status.setText(f"Batch completed: {len(results)} videos processed, {total_photos} total photographs saved.")
        self.batch_completed.emit(results)
