"""
Modern Ribbon-style top tab panel for Vitupi GUI (inspired by modern studio and Office ribbons).
Includes comprehensive preset management with persistent storage and full parameter customization.
"""

from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from vitupi.config import DomainPreset, ExtractionMode, VitupiConfig, get_preset_defaults
from vitupi.gui.icons import get_svg_icon, get_svg_pixmap
from vitupi.presets import PresetManager, get_preset_manager


class SavePresetDialog(QDialog):
    """Clean modal dialog to save parameters as a persistent custom preset."""

    def __init__(self, current_name: str, reserved_names: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Custom Preset")
        self.reserved_names = set(r.lower() for r in reserved_names if r.lower() != "custom")
        self.setFixedWidth(380)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a202c;
                color: #e2e8f0;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 6px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #63b3ed;
            }
            QPushButton {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 6px;
                padding: 7px 16px;
                color: #e2e8f0;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #4a5568;
            }
            QPushButton#saveBtn {
                background-color: #2b6cb0;
                border: 1px solid #3182ce;
                color: #ffffff;
            }
            QPushButton#saveBtn:hover {
                background-color: #3182ce;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Save Preset Configuration")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #63b3ed;")
        layout.addWidget(title)

        desc = QLabel(
            "Enter a name for this custom preset. It will be saved permanently "
            "to your persistent settings file and will appear in the preset dropdown."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #a0aec0; font-size: 12px;")
        layout.addWidget(desc)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Preset Name:"))
        self.name_edit = QLineEdit()
        default_txt = (
            current_name
            if current_name not in ["portrait", "candid", "sports", "security", "default"]
            else "custom"
        )
        self.name_edit.setText(default_txt)
        self.name_edit.selectAll()
        input_layout.addWidget(self.name_edit)
        layout.addLayout(input_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Save Preset")
        self.btn_save.setObjectName("saveBtn")
        self.btn_save.setIcon(get_svg_icon("save", 14, "#ffffff"))
        self.btn_save.clicked.connect(self._validate_and_accept)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def _validate_and_accept(self):
        name = self.name_edit.text().strip().lower()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Preset name cannot be empty.")
            return
        if name in self.reserved_names:
            QMessageBox.warning(
                self,
                "Reserved Name",
                f"'{name}' is a system built-in preset. Please choose a custom name.",
            )
            return
        self.accept()

    def get_preset_name(self) -> str:
        return self.name_edit.text().strip().lower()


class RibbonPanel(QTabWidget):
    """Top ribbon bar housing extraction commands, parameter tuning, review tools, and export."""

    start_extraction_clicked = pyqtSignal()
    cancel_extraction_clicked = pyqtSignal()
    switch_view_clicked = pyqtSignal(int)  # 0: Gallery, 1: Compare
    select_all_clicked = pyqtSignal()
    deselect_all_clicked = pyqtSignal()
    invert_selection_clicked = pyqtSignal()
    export_selected_clicked = pyqtSignal()
    open_folder_clicked = pyqtSignal()
    filter_sharpness_changed = pyqtSignal(float)
    toggle_fullscreen_clicked = pyqtSignal()
    batch_queue_clicked = pyqtSignal()
    benchmark_clicked = pyqtSignal()
    toggle_timeline_clicked = pyqtSignal()
    preset_saved = pyqtSignal(str)
    preset_deleted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocumentMode(True)
        self.preset_manager = get_preset_manager()
        self._loading_preset = True

        self._init_ui()
        self._refresh_preset_combo("portrait")
        self._loading_preset = False

    def _init_ui(self):
        self.setStyleSheet("""
            QTabWidget::pane {
                border-top: 2px solid #2d3748;
                background: #1a202c;
            }
            QTabBar::tab {
                background: #171923;
                color: #a0aec0;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-bottom: 3px solid transparent;
            }
            QTabBar::tab:selected {
                color: #63b3ed;
                background: #1a202c;
                border-bottom: 3px solid #3182ce;
            }
            QTabBar::tab:hover {
                color: #e2e8f0;
                background: #232a3b;
            }
        """)

        # Tab 1: Home / Quick Extract
        self.home_tab = QWidget()
        self._setup_home_tab()
        self.addTab(self.home_tab, get_svg_icon("rocket", 16, "#63b3ed"), "Home & Extract")

        # Tab 2: Parameters & Tuning
        self.tuning_tab = QWidget()
        self._setup_tuning_tab()
        self.addTab(self.tuning_tab, get_svg_icon("tuning", 16, "#63b3ed"), "Parameters & Tuning")

        # Tab 3: Review & Compare
        self.review_tab = QWidget()
        self._setup_review_tab()
        self.addTab(self.review_tab, get_svg_icon("compare", 16, "#63b3ed"), "Review & Compare")

        # Tab 4: Export & Output
        self.export_tab = QWidget()
        self._setup_export_tab()
        self.addTab(self.export_tab, get_svg_icon("export", 16, "#63b3ed"), "Export & Output")

    def _setup_home_tab(self):
        layout = QHBoxLayout(self.home_tab)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Video File Selection Box
        video_box = QGroupBox("Video Source & Destination")
        video_layout = QGridLayout(video_box)

        self.video_path_edit = QLineEdit()
        self.video_path_edit.setPlaceholderText("Select video file (.mp4, .mov, .mkv, .avi)...")
        self.btn_browse_video = QPushButton(" Browse...")
        self.btn_browse_video.setIcon(get_svg_icon("video", 14, "#63b3ed"))
        self.btn_browse_video.clicked.connect(self._on_browse_video)

        self.output_dir_edit = QLineEdit("candids")
        self.btn_browse_output = QPushButton(" Browse...")
        self.btn_browse_output.setIcon(get_svg_icon("folder", 14, "#63b3ed"))
        self.btn_browse_output.clicked.connect(self._on_browse_output)

        video_layout.addWidget(QLabel("Video:"), 0, 0)
        video_layout.addWidget(self.video_path_edit, 0, 1)
        video_layout.addWidget(self.btn_browse_video, 0, 2)
        video_layout.addWidget(QLabel("Output:"), 1, 0)
        video_layout.addWidget(self.output_dir_edit, 1, 1)
        video_layout.addWidget(self.btn_browse_output, 1, 2)
        layout.addWidget(video_box, stretch=2)

        # Profile / Preset Selection Box
        preset_box = QGroupBox("Extraction Profile & Presets")
        preset_layout = QGridLayout(preset_box)

        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(110)
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)

        preset_btn_layout = QHBoxLayout()
        preset_btn_layout.setContentsMargins(0, 0, 0, 0)
        preset_btn_layout.setSpacing(6)

        self.btn_save_preset = QPushButton(" Save Preset...")
        self.btn_save_preset.setIcon(get_svg_icon("save", 13, "#48bb78"))
        self.btn_save_preset.setToolTip("Save the current parameters as a persistent custom preset")
        self.btn_save_preset.clicked.connect(self._on_save_preset_clicked)

        self.btn_delete_preset = QPushButton(" Delete")
        self.btn_delete_preset.setIcon(get_svg_icon("trash", 13, "#e53e3e"))
        self.btn_delete_preset.setToolTip("Delete this custom preset from disk")
        self.btn_delete_preset.setEnabled(False)
        self.btn_delete_preset.clicked.connect(self._on_delete_preset_clicked)

        preset_btn_layout.addWidget(self.btn_save_preset)
        preset_btn_layout.addWidget(self.btn_delete_preset)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["balanced", "exhaustive", "conservative"])
        self.mode_combo.setCurrentText("balanced")
        self.mode_combo.currentIndexChanged.connect(self._on_parameter_manually_tweaked)

        self.max_photos_spin = QSpinBox()
        self.max_photos_spin.setRange(0, 1000)
        self.max_photos_spin.setValue(100)
        self.max_photos_spin.setSpecialValueText("Unlimited")
        self.max_photos_spin.valueChanged.connect(self._on_parameter_manually_tweaked)

        preset_layout.addWidget(QLabel("Preset:"), 0, 0)
        preset_layout.addWidget(self.preset_combo, 0, 1)
        preset_layout.addLayout(preset_btn_layout, 1, 0, 1, 2)
        preset_layout.addWidget(QLabel("Mode:"), 2, 0)
        preset_layout.addWidget(self.mode_combo, 2, 1)
        preset_layout.addWidget(QLabel("Max Photos:"), 3, 0)
        preset_layout.addWidget(self.max_photos_spin, 3, 1)
        layout.addWidget(preset_box, stretch=1)

        # Action & Progress Box
        action_box = QGroupBox("Execution")
        action_layout = QVBoxLayout(action_box)

        self.btn_start = QPushButton(" Start Extraction")
        self.btn_start.setIcon(get_svg_icon("play", 15, "#ffffff"))
        self.btn_start.setMinimumHeight(38)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3182ce, stop:1 #63b3ed);
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background: #4299e1;
            }
            QPushButton:pressed {
                background: #2b6cb0;
            }
            QPushButton:disabled {
                background: #4a5568;
                color: #a0aec0;
            }
        """)
        self.btn_start.clicked.connect(self.start_extraction_clicked.emit)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)

        self.status_label = QLabel("Ready to extract.")
        self.status_label.setStyleSheet("color: #a0aec0; font-size: 12px;")

        action_layout.addWidget(self.btn_start)

        # Batch Queue & Benchmark Quick Buttons
        batch_bench_row = QHBoxLayout()
        batch_bench_row.setSpacing(6)

        self.btn_batch = QPushButton(" Batch Queue...")
        self.btn_batch.setIcon(get_svg_icon("batch", 13, "#00E5FF"))
        self.btn_batch.setToolTip("Process multiple videos concurrently with multi-worker threads")
        self.btn_batch.clicked.connect(self.batch_queue_clicked.emit)

        self.btn_benchmark = QPushButton(" Benchmark...")
        self.btn_benchmark.setIcon(get_svg_icon("benchmark", 13, "#ECC94B"))
        self.btn_benchmark.setToolTip("Run performance, FPS throughput, and quality analytics")
        self.btn_benchmark.clicked.connect(self.benchmark_clicked.emit)

        batch_bench_row.addWidget(self.btn_batch)
        batch_bench_row.addWidget(self.btn_benchmark)
        action_layout.addLayout(batch_bench_row)

        action_layout.addWidget(self.progress_bar)
        action_layout.addWidget(self.status_label)
        layout.addWidget(action_box, stretch=1)

    def _setup_tuning_tab(self):
        layout = QHBoxLayout(self.tuning_tab)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # 1. Sampling Rates Box
        rate_box = QGroupBox("Sampling Rates (FPS & Gaps)")
        rate_layout = QGridLayout(rate_box)

        self.spin_base_fps = QDoubleSpinBox()
        self.spin_base_fps.setRange(0.1, 60.0)
        self.spin_base_fps.setValue(2.0)
        self.spin_base_fps.setSingleStep(0.5)
        self.spin_base_fps.valueChanged.connect(self._on_parameter_manually_tweaked)

        self.spin_dense_fps = QDoubleSpinBox()
        self.spin_dense_fps.setRange(0.5, 60.0)
        self.spin_dense_fps.setValue(6.0)
        self.spin_dense_fps.setSingleStep(1.0)
        self.spin_dense_fps.valueChanged.connect(self._on_parameter_manually_tweaked)

        self.spin_max_gap = QDoubleSpinBox()
        self.spin_max_gap.setRange(0.2, 30.0)
        self.spin_max_gap.setValue(1.0)
        self.spin_max_gap.setSuffix(" s")
        self.spin_max_gap.valueChanged.connect(self._on_parameter_manually_tweaked)

        self.spin_min_dist = QDoubleSpinBox()
        self.spin_min_dist.setRange(0.05, 10.0)
        self.spin_min_dist.setValue(0.4)
        self.spin_min_dist.setSuffix(" s")
        self.spin_min_dist.valueChanged.connect(self._on_parameter_manually_tweaked)

        rate_layout.addWidget(QLabel("Base Scan FPS:"), 0, 0)
        rate_layout.addWidget(self.spin_base_fps, 0, 1)
        rate_layout.addWidget(QLabel("Burst Event FPS:"), 1, 0)
        rate_layout.addWidget(self.spin_dense_fps, 1, 1)
        rate_layout.addWidget(QLabel("Max Shot Gap:"), 2, 0)
        rate_layout.addWidget(self.spin_max_gap, 2, 1)
        rate_layout.addWidget(QLabel("Min Separation:"), 3, 0)
        rate_layout.addWidget(self.spin_min_dist, 3, 1)
        layout.addWidget(rate_box)

        # 2. Quality & Sensitivity Thresholds
        thresh_box = QGroupBox("Quality & Sensitivity Thresholds")
        thresh_layout = QGridLayout(thresh_box)

        self.spin_sensitivity = QDoubleSpinBox()
        self.spin_sensitivity.setRange(0.005, 1.0)
        self.spin_sensitivity.setValue(0.025)
        self.spin_sensitivity.setSingleStep(0.005)
        self.spin_sensitivity.setDecimals(3)
        self.spin_sensitivity.valueChanged.connect(self._on_parameter_manually_tweaked)

        self.spin_min_sharpness = QDoubleSpinBox()
        self.spin_min_sharpness.setRange(0.0, 500.0)
        self.spin_min_sharpness.setValue(18.0)
        self.spin_min_sharpness.valueChanged.connect(self._on_parameter_manually_tweaked)

        self.spin_dedup = QSpinBox()
        self.spin_dedup.setRange(1, 32)
        self.spin_dedup.setValue(6)
        self.spin_dedup.valueChanged.connect(self._on_parameter_manually_tweaked)

        self.spin_scene = QDoubleSpinBox()
        self.spin_scene.setRange(5.0, 100.0)
        self.spin_scene.setValue(27.0)
        self.spin_scene.valueChanged.connect(self._on_parameter_manually_tweaked)

        self.spin_blur_penalty = QDoubleSpinBox()
        self.spin_blur_penalty.setRange(0.0, 5.0)
        self.spin_blur_penalty.setValue(1.0)
        self.spin_blur_penalty.setSingleStep(0.25)
        self.spin_blur_penalty.valueChanged.connect(self._on_parameter_manually_tweaked)

        thresh_layout.addWidget(QLabel("Novelty Sensitivity:"), 0, 0)
        thresh_layout.addWidget(self.spin_sensitivity, 0, 1)
        thresh_layout.addWidget(QLabel("Min Focus (Sharpness):"), 1, 0)
        thresh_layout.addWidget(self.spin_min_sharpness, 1, 1)
        thresh_layout.addWidget(QLabel("Dedup Hamming Distance:"), 2, 0)
        thresh_layout.addWidget(self.spin_dedup, 2, 1)
        thresh_layout.addWidget(QLabel("Scene Cut Sensitivity:"), 3, 0)
        thresh_layout.addWidget(self.spin_scene, 3, 1)
        thresh_layout.addWidget(QLabel("Motion Blur Penalty:"), 4, 0)
        thresh_layout.addWidget(self.spin_blur_penalty, 4, 1)
        layout.addWidget(thresh_box)

        # 3. Intelligent Filters & Stages
        feat_box = QGroupBox("Intelligent Filters & Stages")
        feat_layout = QVBoxLayout(feat_box)

        self.chk_flattery = QCheckBox("Facial Flattery & Portrait Focus")
        self.chk_flattery.setChecked(True)
        self.chk_flattery.toggled.connect(self._on_parameter_manually_tweaked)

        self.chk_action_peaks = QCheckBox("Sports Action-Peak Detection")
        self.chk_action_peaks.setChecked(False)
        self.chk_action_peaks.toggled.connect(self._on_parameter_manually_tweaked)

        self.chk_dedup = QCheckBox("Near-Duplicate Suppression")
        self.chk_dedup.setChecked(True)
        self.chk_dedup.toggled.connect(self._on_parameter_manually_tweaked)

        self.chk_scene_det = QCheckBox("Scene Cut Boundary Detection")
        self.chk_scene_det.setChecked(True)
        self.chk_scene_det.toggled.connect(self._on_parameter_manually_tweaked)

        self.chk_adaptive_sampling = QCheckBox("Adaptive Event Burst Sampling")
        self.chk_adaptive_sampling.setChecked(True)
        self.chk_adaptive_sampling.toggled.connect(self._on_parameter_manually_tweaked)

        self.chk_quality_scoring = QCheckBox("Multi-Metric Quality Scoring")
        self.chk_quality_scoring.setChecked(True)
        self.chk_quality_scoring.toggled.connect(self._on_parameter_manually_tweaked)

        feat_layout.addWidget(self.chk_flattery)
        feat_layout.addWidget(self.chk_action_peaks)
        feat_layout.addWidget(self.chk_dedup)
        feat_layout.addWidget(self.chk_scene_det)
        feat_layout.addWidget(self.chk_adaptive_sampling)
        feat_layout.addWidget(self.chk_quality_scoring)
        layout.addWidget(feat_box)

        # 4. Preset Actions Box in Tuning Tab
        custom_box = QGroupBox("Preset Actions")
        custom_layout = QVBoxLayout(custom_box)

        self.lbl_active_preset = QLabel("Active: portrait")
        self.lbl_active_preset.setStyleSheet("color: #63b3ed; font-weight: bold; font-size: 13px;")

        btn_tuning_save = QPushButton(" Save As Preset...")
        btn_tuning_save.setIcon(get_svg_icon("save", 14, "#48bb78"))
        btn_tuning_save.clicked.connect(self._on_save_preset_clicked)

        btn_tuning_reset = QPushButton(" Reset Current Defaults")
        btn_tuning_reset.setIcon(get_svg_icon("refresh", 14, "#ecc94b"))
        btn_tuning_reset.clicked.connect(self._on_reset_to_preset_defaults)

        custom_layout.addWidget(self.lbl_active_preset)
        custom_layout.addWidget(btn_tuning_save)
        custom_layout.addWidget(btn_tuning_reset)
        custom_layout.addStretch()
        layout.addWidget(custom_box)

    def _setup_review_tab(self):
        layout = QHBoxLayout(self.review_tab)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Selection Helpers
        sel_box = QGroupBox("Batch Selection Tools")
        sel_layout = QHBoxLayout(sel_box)

        btn_select_all = QPushButton(" Select All")
        btn_select_all.setIcon(get_svg_icon("check-square", 14, "#48bb78"))
        btn_select_all.clicked.connect(self.select_all_clicked.emit)

        btn_deselect_all = QPushButton(" Deselect All")
        btn_deselect_all.setIcon(get_svg_icon("x-circle", 14, "#e53e3e"))
        btn_deselect_all.clicked.connect(self.deselect_all_clicked.emit)

        btn_invert = QPushButton(" Invert")
        btn_invert.setIcon(get_svg_icon("invert", 14, "#ecc94b"))
        btn_invert.clicked.connect(self.invert_selection_clicked.emit)

        sel_layout.addWidget(btn_select_all)
        sel_layout.addWidget(btn_deselect_all)
        sel_layout.addWidget(btn_invert)
        layout.addWidget(sel_box)

        # View Mode & Window Switcher
        view_box = QGroupBox("Display & Window")
        view_layout = QHBoxLayout(view_box)

        btn_gallery = QPushButton(" Gallery Grid")
        btn_gallery.setIcon(get_svg_icon("sparkles", 14, "#63b3ed"))
        btn_gallery.clicked.connect(lambda: self.switch_view_clicked.emit(0))

        btn_compare = QPushButton(" A/B Comparison")
        btn_compare.setIcon(get_svg_icon("compare", 14, "#63b3ed"))
        btn_compare.clicked.connect(lambda: self.switch_view_clicked.emit(1))

        self.btn_fullscreen = QPushButton(" Full Screen (F11)")
        self.btn_fullscreen.setIcon(get_svg_icon("fullscreen", 14, "#63b3ed"))
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen_clicked.emit)

        self.btn_timeline = QPushButton(" Timeline")
        self.btn_timeline.setIcon(get_svg_icon("timeline", 14, "#00E5FF"))
        self.btn_timeline.setCheckable(True)
        self.btn_timeline.setChecked(True)
        self.btn_timeline.setToolTip("Toggle chronological video timeline scrubber")
        self.btn_timeline.toggled.connect(lambda chk: self.toggle_timeline_clicked.emit())

        view_layout.addWidget(btn_gallery)
        view_layout.addWidget(btn_compare)
        view_layout.addWidget(self.btn_timeline)
        view_layout.addWidget(self.btn_fullscreen)
        layout.addWidget(view_box)

        # Live Sharpness Filter
        filter_box = QGroupBox("Filter Visible by Sharpness")
        filter_layout = QHBoxLayout(filter_box)

        self.slider_filter_sharpness = QSlider(Qt.Orientation.Horizontal)
        self.slider_filter_sharpness.setRange(0, 150)
        self.slider_filter_sharpness.setValue(0)
        self.lbl_filter_val = QLabel("0.0")

        self.slider_filter_sharpness.valueChanged.connect(
            lambda v: (self.lbl_filter_val.setText(f"{v:.1f}"), self.filter_sharpness_changed.emit(float(v)))
        )

        filter_layout.addWidget(QLabel("Min Focus:"))
        filter_layout.addWidget(self.slider_filter_sharpness)
        filter_layout.addWidget(self.lbl_filter_val)
        layout.addWidget(filter_box)

    def _setup_export_tab(self):
        layout = QHBoxLayout(self.export_tab)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Export Format
        fmt_box = QGroupBox("Output Format & Options")
        fmt_layout = QGridLayout(fmt_box)

        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["JPEG (High Quality 95%)", "PNG (Lossless)"])

        self.chk_contact_sheet = QCheckBox("Generate Overview Contact Sheet (contact_sheet.jpg)")
        self.chk_contact_sheet.setChecked(True)

        self.chk_json_report = QCheckBox("Generate Machine-Readable Report (vitupi_report.json)")
        self.chk_json_report.setChecked(True)

        fmt_layout.addWidget(QLabel("Image Format:"), 0, 0)
        fmt_layout.addWidget(self.fmt_combo, 0, 1)
        fmt_layout.addWidget(self.chk_contact_sheet, 1, 0, 1, 2)
        fmt_layout.addWidget(self.chk_json_report, 2, 0, 1, 2)
        layout.addWidget(fmt_box, stretch=1)

        # Quick Actions
        actions_box = QGroupBox("Export Actions")
        actions_layout = QHBoxLayout(actions_box)

        self.btn_export_selected = QPushButton(" Export Selected Photos...")
        self.btn_export_selected.setIcon(get_svg_icon("export", 15, "#ffffff"))
        self.btn_export_selected.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                font-weight: bold;
                padding: 10px 18px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #3182ce;
            }
        """)
        self.btn_export_selected.clicked.connect(self.export_selected_clicked.emit)

        self.btn_open_folder = QPushButton(" Open Output Directory")
        self.btn_open_folder.setIcon(get_svg_icon("folder", 14, "#e2e8f0"))
        self.btn_open_folder.clicked.connect(self.open_folder_clicked.emit)

        actions_layout.addWidget(self.btn_export_selected)
        actions_layout.addWidget(self.btn_open_folder)
        layout.addWidget(actions_box, stretch=2)

    def _refresh_preset_combo(self, select_name: Optional[str] = None):
        """Reload the preset combo box with built-in and user-saved presets."""
        was_loading = self._loading_preset
        self._loading_preset = True

        current = select_name or self.preset_combo.currentText() or "portrait"
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()

        presets = self.preset_manager.list_all_presets()
        self.preset_combo.addItems(presets)

        if current in presets:
            self.preset_combo.setCurrentText(current)
        else:
            self.preset_combo.setCurrentText("portrait")

        self.preset_combo.blockSignals(False)
        self._loading_preset = was_loading

        self._on_preset_changed(self.preset_combo.currentText())

    def _apply_config_to_ui(self, config: VitupiConfig):
        """Populate all ribbon input controls from a given VitupiConfig instance."""
        was_loading = self._loading_preset
        self._loading_preset = True

        mode_val = config.mode.value if isinstance(config.mode, ExtractionMode) else str(config.mode)
        self.mode_combo.setCurrentText(mode_val)

        if config.max_photos is None:
            self.max_photos_spin.setValue(0)
        else:
            self.max_photos_spin.setValue(config.max_photos)

        if config.base_fps is not None:
            self.spin_base_fps.setValue(config.base_fps)
        if config.dense_fps is not None:
            self.spin_dense_fps.setValue(config.dense_fps)
        if config.max_temporal_gap is not None:
            self.spin_max_gap.setValue(config.max_temporal_gap)
        if config.min_temporal_distance is not None:
            self.spin_min_dist.setValue(config.min_temporal_distance)
        if config.novelty_threshold is not None:
            self.spin_sensitivity.setValue(config.novelty_threshold)
        if config.min_sharpness_score is not None:
            self.spin_min_sharpness.setValue(config.min_sharpness_score)
        if config.dedup_threshold is not None:
            self.spin_dedup.setValue(config.dedup_threshold)
        if config.scene_threshold is not None:
            self.spin_scene.setValue(config.scene_threshold)
        if config.motion_blur_penalty is not None:
            self.spin_blur_penalty.setValue(config.motion_blur_penalty)

        self.chk_flattery.setChecked(bool(config.flattery_filter))
        self.chk_action_peaks.setChecked(bool(config.action_peak_detection))
        self.chk_dedup.setChecked(bool(config.duplicate_removal))
        self.chk_scene_det.setChecked(bool(config.scene_detection))
        self.chk_adaptive_sampling.setChecked(bool(config.adaptive_sampling))
        self.chk_quality_scoring.setChecked(bool(config.quality_scoring))
        self.chk_contact_sheet.setChecked(bool(config.generate_contact_sheet))
        self.chk_json_report.setChecked(bool(config.generate_json_report))

        self._loading_preset = was_loading

    def _update_preset_ui_state(self, preset_name: str):
        """Update active indicator label and delete button state."""
        if hasattr(self, "lbl_active_preset"):
            self.lbl_active_preset.setText(f"Active: {preset_name}")
        if hasattr(self, "btn_delete_preset"):
            # Delete button is enabled only for custom user-created presets (not built-in)
            self.btn_delete_preset.setEnabled(not self.preset_manager.is_builtin(preset_name))

    def _on_preset_changed(self, preset_name: str):
        """Fired when the user selects a preset from the dropdown."""
        if self._loading_preset or not preset_name:
            return
        config = self.preset_manager.get_preset_config(preset_name)
        self._apply_config_to_ui(config)
        self._update_preset_ui_state(preset_name)

    def _on_parameter_manually_tweaked(self):
        """Called whenever the user modifies any spinbox, combo, or checkbox."""
        if self._loading_preset:
            return
        current = self.preset_combo.currentText()
        if current in ["portrait", "candid", "sports", "security", "default"]:
            self._loading_preset = True
            self.preset_combo.setCurrentText("custom")
            self._loading_preset = False
            self._update_preset_ui_state("custom")

    def _on_save_preset_clicked(self):
        """Open dialog to persist the current parameter configuration."""
        current = self.preset_combo.currentText()
        dlg = SavePresetDialog(
            current_name=current,
            reserved_names=self.preset_manager.BUILTIN_PRESETS,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            preset_name = dlg.get_preset_name()
            config = self.build_config()
            self.preset_manager.save_preset(preset_name, config)
            self._refresh_preset_combo(select_name=preset_name)
            self.preset_saved.emit(preset_name)

    def _on_delete_preset_clicked(self):
        """Delete currently selected user preset."""
        current = self.preset_combo.currentText()
        if self.preset_manager.is_builtin(current):
            return

        reply = QMessageBox.question(
            self,
            "Delete Preset",
            f"Are you sure you want to permanently delete custom preset '{current}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.preset_manager.delete_preset(current)
            self._refresh_preset_combo(select_name="portrait")
            self.preset_deleted.emit(current)

    def _on_reset_to_preset_defaults(self):
        """Reset current parameter inputs to official defaults for active preset."""
        current = self.preset_combo.currentText()
        config = self.preset_manager.get_preset_config(current)
        self._apply_config_to_ui(config)

    def _on_browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.mov *.mkv *.avi *.webm *.m4v);;All Files (*)",
        )
        if file_path:
            self.video_path_edit.setText(file_path)

    def _on_browse_output(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_edit.setText(directory)

    def build_config(self) -> VitupiConfig:
        """Construct VitupiConfig with all user overrides from the ribbon."""
        mode_str = self.mode_combo.currentText()
        preset_str = self.preset_combo.currentText()
        max_photos = self.max_photos_spin.value()
        if max_photos == 0:
            max_photos = None

        is_builtin = preset_str in [e.value for e in DomainPreset]
        domain_preset = DomainPreset(preset_str) if is_builtin else DomainPreset.CUSTOM
        custom_name = None if is_builtin else preset_str

        return VitupiConfig(
            mode=ExtractionMode(mode_str),
            preset=domain_preset,
            custom_name=custom_name,
            max_photos=max_photos,
            base_fps=self.spin_base_fps.value(),
            dense_fps=self.spin_dense_fps.value(),
            max_temporal_gap=self.spin_max_gap.value(),
            min_temporal_distance=self.spin_min_dist.value(),
            novelty_threshold=self.spin_sensitivity.value(),
            min_sharpness_score=self.spin_min_sharpness.value(),
            dedup_threshold=self.spin_dedup.value(),
            scene_threshold=self.spin_scene.value(),
            motion_blur_penalty=self.spin_blur_penalty.value(),
            flattery_filter=self.chk_flattery.isChecked(),
            action_peak_detection=self.chk_action_peaks.isChecked(),
            duplicate_removal=self.chk_dedup.isChecked(),
            scene_detection=self.chk_scene_det.isChecked(),
            adaptive_sampling=self.chk_adaptive_sampling.isChecked(),
            quality_scoring=self.chk_quality_scoring.isChecked(),
            generate_contact_sheet=self.chk_contact_sheet.isChecked(),
            generate_json_report=self.chk_json_report.isChecked(),
        )

    def update_fullscreen_state(self, is_fullscreen: bool):
        """Update the Full Screen button text and icon based on window state."""
        if hasattr(self, "btn_fullscreen"):
            if is_fullscreen:
                self.btn_fullscreen.setIcon(get_svg_icon("fullscreen-exit", 14, "#63b3ed"))
                self.btn_fullscreen.setText(" Exit Full Screen (F11)")
            else:
                self.btn_fullscreen.setIcon(get_svg_icon("fullscreen", 14, "#63b3ed"))
                self.btn_fullscreen.setText(" Full Screen (F11)")
