"""
Benchmark & Performance Analytics Dialog for Vitupi GUI.
Executes formal performance benchmarking and renders metric cards with JSON export capabilities.
"""

import os
from typing import Optional
from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from vitupi.benchmark import BenchmarkReport, run_benchmark
from vitupi.config import VitupiConfig
from vitupi.gui.icons import get_svg_icon


class BenchmarkWorker(QThread):
    """Worker thread for running formal extraction benchmarks without blocking UI."""

    finished_report = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, video_path: str, config: VitupiConfig):
        super().__init__()
        self.video_path = video_path
        self.config = config

    def run(self):
        try:
            report = run_benchmark(self.video_path, config=self.config)
            self.finished_report.emit(report)
        except Exception as e:
            self.failed.emit(str(e))


class BenchmarkDialog(QDialog):
    """Dialog displaying performance, throughput, and quality analytics."""

    def __init__(self, video_path: str, config: Optional[VitupiConfig] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.video_path = video_path
        self.config = config or VitupiConfig()
        self._report: Optional[BenchmarkReport] = None
        self._worker: Optional[BenchmarkWorker] = None

        self.setWindowTitle("Benchmark & Performance Analytics - Vitupi")
        self.resize(760, 560)
        self.setMinimumSize(640, 480)

        self._init_ui()
        self._start_benchmark()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # Title & Video Header
        header = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(get_svg_icon("benchmark", size=24, color="#00E5FF").pixmap(24, 24))
        header.addWidget(title_icon)

        title_lbl = QLabel(f"Benchmark: {os.path.basename(self.video_path)}")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #F7FAFC;")
        header.addWidget(title_lbl, 1)

        layout.addLayout(header)

        # Progress bar during benchmark run
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setRange(0, 0)  # Indeterminate spinner
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #16181E; border: 1px solid #2D3748; border-radius: 3px; }"
            "QProgressBar::chunk { background-color: #00E5FF; }"
        )
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Evaluating video decoding speed, candidate generation, and deduplication...")
        self.lbl_status.setStyleSheet("color: #A0AEC0; font-size: 11px;")
        layout.addWidget(self.lbl_status)

        # Metric Cards Grid
        self.grid_cards = QGridLayout()
        self.grid_cards.setSpacing(10)

        self.card_fps = self._create_metric_card("Throughput Speed", "-- FPS", "Decoding & extraction rate")
        self.card_speedup = self._create_metric_card("Realtime Speedup", "--x", "Compared to video duration")
        self.card_photos = self._create_metric_card("Photos Exported", "--", "High-quality selections")
        self.card_dedup = self._create_metric_card("Deduplication Rate", "--%", "Near-duplicates purged")
        self.card_scenes = self._create_metric_card("Scene Coverage", "--%", "Scenes with selected photos")
        self.card_quality = self._create_metric_card("Mean Quality Score", "-- / 100", "Composite visual score")

        self.grid_cards.addWidget(self.card_fps, 0, 0)
        self.grid_cards.addWidget(self.card_speedup, 0, 1)
        self.grid_cards.addWidget(self.card_photos, 0, 2)
        self.grid_cards.addWidget(self.card_dedup, 1, 0)
        self.grid_cards.addWidget(self.card_scenes, 1, 1)
        self.grid_cards.addWidget(self.card_quality, 1, 2)

        layout.addLayout(self.grid_cards)

        # ASCII Formatted Report
        self.text_report = QTextEdit()
        self.text_report.setReadOnly(True)
        self.text_report.setFontFamily("Consolas, Courier New, monospace")
        self.text_report.setStyleSheet(
            "QTextEdit { background-color: #12141A; color: #E2E8F0; border: 1px solid #2D3748; border-radius: 4px; font-family: Consolas, monospace; font-size: 11px; }"
        )
        layout.addWidget(self.text_report, 1)

        # Bottom Bar
        bottom = QHBoxLayout()
        self.btn_export_json = QPushButton("Export JSON Report...")
        self.btn_export_json.setIcon(get_svg_icon("save", size=16, color="#00E5FF"))
        self.btn_export_json.setEnabled(False)
        self.btn_export_json.clicked.connect(self._on_export_json)
        bottom.addWidget(self.btn_export_json)

        bottom.addStretch()

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        bottom.addWidget(self.btn_close)

        layout.addLayout(bottom)

    def _create_metric_card(self, title: str, value: str, subtitle: str) -> QGroupBox:
        box = QGroupBox()
        box.setStyleSheet(
            "QGroupBox { background-color: #1A1E26; border: 1px solid #2D3748; border-radius: 6px; padding: 10px; }"
        )
        vbox = QVBoxLayout(box)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #718096; font-size: 10px; font-weight: bold; text-transform: uppercase;")
        lbl_val = QLabel(value)
        lbl_val.setObjectName("val")
        lbl_val.setStyleSheet("color: #00E5FF; font-size: 18px; font-weight: bold;")
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: #A0AEC0; font-size: 10px;")

        vbox.addWidget(lbl_title)
        vbox.addWidget(lbl_val)
        vbox.addWidget(lbl_sub)
        return box

    def _update_card_value(self, card: QGroupBox, val: str):
        lbl = card.findChild(QLabel, "val")
        if lbl:
            lbl.setText(val)

    def _start_benchmark(self):
        self._worker = BenchmarkWorker(self.video_path, self.config)
        self._worker.finished_report.connect(self._on_benchmark_finished)
        self._worker.failed.connect(self._on_benchmark_failed)
        self._worker.start()

    def _on_benchmark_finished(self, report: BenchmarkReport):
        self._report = report
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.lbl_status.setText(f"Benchmark completed in {report.processing_time_sec:.2f} seconds.")

        # Update Metric Cards
        self._update_card_value(self.card_fps, f"{report.fps:.1f} FPS")
        self._update_card_value(self.card_speedup, f"{report.speed_factor:.2f}x")
        self._update_card_value(self.card_photos, f"{report.photos_exported}")
        self._update_card_value(self.card_dedup, f"{report.duplicate_suppression_rate_pct:.1f}%")
        self._update_card_value(self.card_scenes, f"{report.scene_coverage_pct:.1f}%")
        self._update_card_value(self.card_quality, f"{report.mean_quality_score:.1f} / 100")

        # Update ASCII Report
        self.text_report.setPlainText(report.format_table())
        self.btn_export_json.setEnabled(True)

    def _on_benchmark_failed(self, error_msg: str):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.lbl_status.setText(f"Benchmark error: {error_msg}")
        QMessageBox.critical(self, "Benchmark Failed", f"Benchmark encountered an error:\n{error_msg}")

    def _on_export_json(self):
        if not self._report:
            return
        default_name = f"{os.path.splitext(os.path.basename(self.video_path))[0]}_benchmark.json"
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Benchmark JSON Report", default_name, "JSON Files (*.json)")
        if save_path:
            self._report.to_json(save_path)
            QMessageBox.information(self, "Report Saved", f"Benchmark report saved to:\n{save_path}")
