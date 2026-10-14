"""
Modern Ribbon-style top tab panel for Vitupi GUI (inspired by modern studio and Office ribbons).
"""

from PyQt6.QtCore import Qt, pyqtSignal
from vitupi.config import DomainPreset, ExtractionMode, VitupiConfig
from vitupi.gui.icons import get_svg_icon, get_svg_pixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocumentMode(True)
        self._init_ui()

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
        preset_box = QGroupBox("Extraction Profile")
        preset_layout = QGridLayout(preset_box)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["portrait", "candid", "sports", "security", "default"])
        self.preset_combo.setCurrentText("portrait")

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["balanced", "exhaustive", "conservative"])
        self.mode_combo.setCurrentText("balanced")

        self.max_photos_spin = QSpinBox()
        self.max_photos_spin.setRange(0, 1000)
        self.max_photos_spin.setValue(100)
        self.max_photos_spin.setSpecialValueText("Unlimited")

        preset_layout.addWidget(QLabel("Preset:"), 0, 0)
        preset_layout.addWidget(self.preset_combo, 0, 1)
        preset_layout.addWidget(QLabel("Mode:"), 1, 0)
        preset_layout.addWidget(self.mode_combo, 1, 1)
        preset_layout.addWidget(QLabel("Max Photos:"), 2, 0)
        preset_layout.addWidget(self.max_photos_spin, 2, 1)
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
        action_layout.addWidget(self.progress_bar)
        action_layout.addWidget(self.status_label)
        layout.addWidget(action_box, stretch=1)

    def _setup_tuning_tab(self):
        layout = QHBoxLayout(self.tuning_tab)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Sampling Rates
        rate_box = QGroupBox("Sampling Rates (FPS & Gaps)")
        rate_layout = QGridLayout(rate_box)

        self.spin_base_fps = QDoubleSpinBox()
        self.spin_base_fps.setRange(0.1, 60.0)
        self.spin_base_fps.setValue(2.0)
        self.spin_base_fps.setSingleStep(0.5)

        self.spin_dense_fps = QDoubleSpinBox()
        self.spin_dense_fps.setRange(0.5, 60.0)
        self.spin_dense_fps.setValue(6.0)
        self.spin_dense_fps.setSingleStep(1.0)

        self.spin_max_gap = QDoubleSpinBox()
        self.spin_max_gap.setRange(0.2, 30.0)
        self.spin_max_gap.setValue(1.0)
        self.spin_max_gap.setSuffix(" s")

        self.spin_min_dist = QDoubleSpinBox()
        self.spin_min_dist.setRange(0.05, 10.0)
        self.spin_min_dist.setValue(0.4)
        self.spin_min_dist.setSuffix(" s")

        rate_layout.addWidget(QLabel("Base Scan FPS:"), 0, 0)
        rate_layout.addWidget(self.spin_base_fps, 0, 1)
        rate_layout.addWidget(QLabel("Burst Event FPS:"), 1, 0)
        rate_layout.addWidget(self.spin_dense_fps, 1, 1)
        rate_layout.addWidget(QLabel("Max Shot Gap:"), 2, 0)
        rate_layout.addWidget(self.spin_max_gap, 2, 1)
        rate_layout.addWidget(QLabel("Min Separation:"), 3, 0)
        rate_layout.addWidget(self.spin_min_dist, 3, 1)
        layout.addWidget(rate_box)

        # Thresholds
        thresh_box = QGroupBox("Quality & Sensitivity Thresholds")
        thresh_layout = QGridLayout(thresh_box)

        self.spin_sensitivity = QDoubleSpinBox()
        self.spin_sensitivity.setRange(0.005, 1.0)
        self.spin_sensitivity.setValue(0.025)
        self.spin_sensitivity.setSingleStep(0.005)
        self.spin_sensitivity.setDecimals(3)

        self.spin_min_sharpness = QDoubleSpinBox()
        self.spin_min_sharpness.setRange(0.0, 500.0)
        self.spin_min_sharpness.setValue(18.0)

        self.spin_dedup = QSpinBox()
        self.spin_dedup.setRange(1, 32)
        self.spin_dedup.setValue(6)

        self.spin_scene = QDoubleSpinBox()
        self.spin_scene.setRange(5.0, 100.0)
        self.spin_scene.setValue(27.0)

        thresh_layout.addWidget(QLabel("Novelty Sensitivity:"), 0, 0)
        thresh_layout.addWidget(self.spin_sensitivity, 0, 1)
        thresh_layout.addWidget(QLabel("Min Focus (Sharpness):"), 1, 0)
        thresh_layout.addWidget(self.spin_min_sharpness, 1, 1)
        thresh_layout.addWidget(QLabel("Dedup Hamming Distance:"), 2, 0)
        thresh_layout.addWidget(self.spin_dedup, 2, 1)
        thresh_layout.addWidget(QLabel("Scene Cut Sensitivity:"), 3, 0)
        thresh_layout.addWidget(self.spin_scene, 3, 1)
        layout.addWidget(thresh_box)

        # Feature Toggles
        feat_box = QGroupBox("Intelligent Filters & Stages")
        feat_layout = QVBoxLayout(feat_box)

        self.chk_flattery = QCheckBox("Facial Flattery & Portrait Focus")
        self.chk_flattery.setChecked(True)

        self.chk_action_peaks = QCheckBox("Sports Action-Peak Detection")
        self.chk_action_peaks.setChecked(False)

        self.chk_dedup = QCheckBox("Near-Duplicate Suppression")
        self.chk_dedup.setChecked(True)

        self.chk_scene_det = QCheckBox("Scene Cut Boundary Detection")
        self.chk_scene_det.setChecked(True)

        feat_layout.addWidget(self.chk_flattery)
        feat_layout.addWidget(self.chk_action_peaks)
        feat_layout.addWidget(self.chk_dedup)
        feat_layout.addWidget(self.chk_scene_det)
        layout.addWidget(feat_box)

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

        view_layout.addWidget(btn_gallery)
        view_layout.addWidget(btn_compare)
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
        layout.addWidget(fmt_box, stretch=2)

        # Export Actions
        act_box = QGroupBox("Save & Open")
        act_layout = QVBoxLayout(act_box)

        self.btn_export_selected = QPushButton(" Save Selected Photos")
        self.btn_export_selected.setIcon(get_svg_icon("export", 16, "#ffffff"))
        self.btn_export_selected.setStyleSheet("""
            QPushButton {
                background: #38a169;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover { background: #48bb78; }
        """)
        self.btn_export_selected.clicked.connect(self.export_selected_clicked.emit)

        btn_open_folder = QPushButton(" Open Output Folder")
        btn_open_folder.setIcon(get_svg_icon("folder", 14, "#cbd5e0"))
        btn_open_folder.clicked.connect(self.open_folder_clicked.emit)

        act_layout.addWidget(self.btn_export_selected)
        act_layout.addWidget(btn_open_folder)
        layout.addWidget(act_box, stretch=1)

    def _on_browse_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.mov *.mkv *.avi *.webm *.m4v);;All Files (*.*)",
        )
        if path:
            self.video_path_edit.setText(path)

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

        return VitupiConfig(
            mode=ExtractionMode(mode_str),
            preset=DomainPreset(preset_str),
            max_photos=max_photos,
            base_fps=self.spin_base_fps.value(),
            dense_fps=self.spin_dense_fps.value(),
            max_temporal_gap=self.spin_max_gap.value(),
            min_temporal_distance=self.spin_min_dist.value(),
            novelty_threshold=self.spin_sensitivity.value(),
            min_sharpness_score=self.spin_min_sharpness.value(),
            dedup_threshold=self.spin_dedup.value(),
            scene_threshold=self.spin_scene.value(),
            flattery_filter=self.chk_flattery.isChecked(),
            action_peak_detection=self.chk_action_peaks.isChecked(),
            duplicate_removal=self.chk_dedup.isChecked(),
            scene_detection=self.chk_scene_det.isChecked(),
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
