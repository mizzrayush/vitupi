"""
Main Application Window for Vitupi GUI.
"""

import os
import shutil
import subprocess
import sys
from typing import List, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from vitupi.config import DomainPreset, ExtractionMode, VitupiConfig
from vitupi.gui.batch_dialog import BatchQueueDialog
from vitupi.gui.benchmark_dialog import BenchmarkDialog
from vitupi.gui.canvas import CentralCanvas
from vitupi.gui.icons import get_svg_icon
from vitupi.gui.ribbon import RibbonPanel
from vitupi.gui.timeline import VideoTimelineWidget
from vitupi.gui.worker import ExtractionWorker
from vitupi.models import ExtractionResult, SelectedPhoto


class VitupiMainWindow(QMainWindow):
    """Main window integrating the top ribbon, central canvas, and background extraction worker."""

    def __init__(self, initial_video: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("Vitupi (V2P) - Intelligent Video to Photographs Studio")
        self.setWindowIcon(get_svg_icon("sparkles", 32, "#63b3ed"))
        self.resize(1360, 880)
        self.setMinimumSize(960, 680)

        self.current_result: Optional[ExtractionResult] = None
        self.worker: Optional[ExtractionWorker] = None

        self._init_ui()
        self._apply_global_theme()

        # Keyboard shortcuts
        self.shortcut_fullscreen = QShortcut(QKeySequence("F11"), self)
        self.shortcut_fullscreen.activated.connect(self.toggle_fullscreen)

        if initial_video and os.path.exists(initial_video):
            self.ribbon.video_path_edit.setText(os.path.abspath(initial_video))

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Ribbon Tab Panel
        self.ribbon = RibbonPanel()
        root_layout.addWidget(self.ribbon)

        # 2. Chronological Video Timeline Scrubber
        self.timeline = VideoTimelineWidget()
        root_layout.addWidget(self.timeline)

        # 3. Central Canvas (Gallery & A/B Comparator)
        self.canvas = CentralCanvas()
        root_layout.addWidget(self.canvas, stretch=1)

        # Connect Ribbon & Canvas signals
        self.ribbon.start_extraction_clicked.connect(self._on_start_extraction)
        self.ribbon.switch_view_clicked.connect(self._on_switch_view)
        self.ribbon.select_all_clicked.connect(lambda: self.canvas.set_all_selected(True))
        self.ribbon.deselect_all_clicked.connect(lambda: self.canvas.set_all_selected(False))
        self.ribbon.invert_selection_clicked.connect(lambda: self.canvas.invert_selection())
        self.ribbon.export_selected_clicked.connect(self._on_export_selected)
        self.ribbon.open_folder_clicked.connect(self._on_open_folder)
        self.ribbon.filter_sharpness_changed.connect(self.canvas.filter_by_sharpness)
        self.ribbon.toggle_fullscreen_clicked.connect(self.toggle_fullscreen)
        self.ribbon.toggle_timeline_clicked.connect(self._on_toggle_timeline)
        self.ribbon.batch_queue_clicked.connect(self._on_open_batch_dialog)
        self.ribbon.benchmark_clicked.connect(self._on_open_benchmark_dialog)
        self.ribbon.preset_saved.connect(
            lambda name: self.status_bar.showMessage(f"Custom preset '{name}' saved to persistent storage.", 4000)
        )
        self.ribbon.preset_deleted.connect(
            lambda name: self.status_bar.showMessage(f"Custom preset '{name}' deleted from disk.", 4000)
        )
        self.canvas.selection_changed.connect(self._on_selection_changed)
        self.canvas.photo_inspected.connect(self.timeline.select_photo)
        self.timeline.photo_selected.connect(self.canvas.preview_photo_by_path)

        # 3. Status Bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background: #171923; color: #a0aec0; border-top: 1px solid #2d3748;")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Select a video file to begin extracting moments.")

    def _apply_global_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #171923;
            }
            QWidget {
                background-color: #171923;
                color: #e2e8f0;
                font-size: 13px;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            }
            QGroupBox {
                border: 1px solid #2d3748;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 12px;
                font-weight: bold;
                font-size: 11px;
                color: #cbd5e0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                background-color: #1a202c;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 6px;
                padding: 5px 8px;
                color: #edf2f7;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #63b3ed;
                background-color: #323f54;
            }
            QPushButton {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 6px;
                padding: 6px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #718096;
            }
            QPushButton:pressed {
                background-color: #1a202c;
            }
            QCheckBox {
                spacing: 8px;
                font-size: 12px;
                color: #e2e8f0;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #4a5568;
                background: #2d3748;
            }
            QCheckBox::indicator:checked {
                background: #3182ce;
                border-color: #63b3ed;
            }
            QScrollBar:vertical {
                border: none;
                background: #171923;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #4a5568;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #718096;
            }
        """)

    def _build_config_from_ui(self) -> VitupiConfig:
        """Construct VitupiConfig with all user overrides from the ribbon."""
        return self.ribbon.build_config()

    def _on_start_extraction(self):
        video_path = self.ribbon.video_path_edit.text().strip()
        output_dir = self.ribbon.output_dir_edit.text().strip() or "photos"

        if not video_path:
            QMessageBox.warning(self, "No Video Selected", "Please select a video file first.")
            return

        if not os.path.exists(video_path):
            QMessageBox.critical(self, "File Not Found", f"Video file does not exist: {video_path}")
            return

        config = self._build_config_from_ui()

        # UI state
        self.ribbon.btn_start.setEnabled(False)
        self.ribbon.progress_bar.setValue(5)
        self.ribbon.status_label.setText("Starting extraction engine...")
        self.status_bar.showMessage(f"Processing: {os.path.basename(video_path)}...")

        # Background thread
        self.worker = ExtractionWorker(video_path=video_path, output_dir=output_dir, config=config)
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.error.connect(self._on_worker_error)
        self.worker.start()

    def _on_worker_progress(self, pct: int, msg: str):
        self.ribbon.progress_bar.setValue(pct)
        self.ribbon.status_label.setText(msg)
        self.status_bar.showMessage(msg)

    def _on_worker_finished(self, result: ExtractionResult):
        self.current_result = result
        self.ribbon.btn_start.setEnabled(True)
        self.ribbon.progress_bar.setValue(100)
        self.ribbon.status_label.setText(f"Complete: {len(result.photos)} photos extracted.")

        self.timeline.set_duration(result.metadata.duration_sec)
        self.timeline.set_photos(result.photos)
        self.canvas.populate_photos(result.photos)
        self._update_status_counts()

        QMessageBox.information(
            self,
            "Extraction Complete",
            f"Successfully extracted {len(result.photos)} high-quality photographs in {result.statistics.processing_time_sec:.1f}s!\n\n"
            f"You can now review candidates in the Gallery, compare similar frames in the A/B Comparator, or export your selection.",
        )

    def _on_worker_error(self, err_msg: str):
        self.ribbon.btn_start.setEnabled(True)
        self.ribbon.progress_bar.setValue(0)
        self.ribbon.status_label.setText("Extraction failed.")
        self.status_bar.showMessage(f"Error: {err_msg}")
        QMessageBox.critical(self, "Extraction Error", f"An error occurred during extraction:\n\n{err_msg}")

    def _on_switch_view(self, index: int):
        self.canvas.setCurrentIndex(index)

    def _on_selection_changed(self, path: str, checked: bool):
        self._update_status_counts()

    def _update_status_counts(self):
        if not self.current_result:
            return
        total = len(self.canvas.cards)
        selected = sum(1 for c in self.canvas.cards.values() if c.is_selected)
        self.status_bar.showMessage(
            f"Total Photos: {total} | Selected for Export: {selected} | Deselected: {total - selected}"
        )

    def _on_export_selected(self):
        if not self.canvas.cards:
            QMessageBox.information(self, "No Photos", "No photographs have been extracted yet.")
            return

        selected_cards = [c for c in self.canvas.cards.values() if c.is_selected]
        if not selected_cards:
            QMessageBox.warning(self, "None Selected", "Please select at least one photograph to export.")
            return

        target_dir = QFileDialog.getExistingDirectory(self, "Select Destination Folder for Export")
        if not target_dir:
            return

        copied = 0
        for card in selected_cards:
            src = card.photo.path
            if os.path.exists(src):
                dst = os.path.join(target_dir, os.path.basename(src))
                shutil.copy2(src, dst)
                copied += 1

        QMessageBox.information(
            self,
            "Export Successful",
            f"Exported {copied} selected photographs to:\n{target_dir}",
        )

    def _on_open_folder(self):
        output_dir = self.ribbon.output_dir_edit.text().strip() or "photos"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        if sys.platform == "win32":
            os.startfile(output_dir)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", output_dir])
        else:
            subprocess.Popen(["xdg-open", output_dir])

    def toggle_fullscreen(self):
        """Toggle between full screen mode and maximized desktop window mode."""
        if self.isFullScreen():
            self.showMaximized()
            self.ribbon.update_fullscreen_state(False)
            self.status_bar.showMessage("Switched to Maximized Window mode. (Press F11 for Full Screen)", 3500)
        else:
            self.showFullScreen()
            self.ribbon.update_fullscreen_state(True)
            self.status_bar.showMessage("Switched to Full Screen mode. (Press F11 or Esc to exit)", 3500)

    def keyPressEvent(self, event):
        """Allow Escape key to exit full screen mode."""
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _on_toggle_timeline(self):
        """Toggle visibility of the chronological video timeline scrubber."""
        self.timeline.setVisible(not self.timeline.isVisible())

    def _on_open_batch_dialog(self):
        """Open the multi-video concurrent batch queue dialog."""
        preset = self.ribbon.preset_combo.currentText()
        dialog = BatchQueueDialog(parent=self, initial_preset=preset)
        dialog.exec()

    def _on_open_benchmark_dialog(self):
        """Open the formal performance and throughput benchmark analytics dialog."""
        video_path = self.ribbon.video_path_edit.text().strip()
        if not video_path or not os.path.isfile(video_path):
            video_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Video to Benchmark",
                "",
                "Video Files (*.mp4 *.mov *.mkv *.avi *.webm *.m4v);;All Files (*)",
            )
            if not video_path:
                return
            self.ribbon.video_path_edit.setText(video_path)

        config = self.ribbon.get_config()
        dialog = BenchmarkDialog(video_path, config=config, parent=self)
        dialog.exec()
