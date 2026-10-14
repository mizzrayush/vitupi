"""
Central Interactive Canvas for Vitupi GUI.
Features:
- Gallery Grid View with Photo Cards and SVG action buttons
- Dedicated Right-Side Live Photo Inspector Panel
- Side-by-Side A/B Candidate Comparator
"""

import os
import subprocess
import sys
from typing import Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from vitupi.gui.icons import get_svg_icon, get_svg_pixmap
from vitupi.models import SelectedPhoto


class PhotoCard(QFrame):
    """Card widget representing an individual extracted photograph."""

    toggled = pyqtSignal(str, bool)       # path, is_selected
    set_compare_a = pyqtSignal(str)        # path
    set_compare_b = pyqtSignal(str)        # path
    preview_requested = pyqtSignal(object) # SelectedPhoto

    def __init__(self, photo: SelectedPhoto, parent=None):
        super().__init__(parent)
        self.photo = photo
        self.is_selected = True
        self._init_ui()

    def _init_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedWidth(230)
        self.setStyleSheet("""
            PhotoCard {
                background-color: #232a3b;
                border: 2px solid #3d4a61;
                border-radius: 8px;
            }
            PhotoCard:hover {
                border: 2px solid #63b3ed;
                background-color: #2c364c;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header: Checkbox + Timestamp Badge + Quick Preview Icon
        header = QHBoxLayout()
        header.setSpacing(6)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.setToolTip("Toggle inclusion for export")
        self.checkbox.toggled.connect(self._on_toggled)

        time_str = f"{self.photo.timestamp_sec:.2f}s"
        lbl_time = QLabel(time_str)
        lbl_time.setStyleSheet("""
            background: #171923;
            color: #e2e8f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
        """)

        # Dedicated Eye / Preview Icon Button
        self.btn_preview = QPushButton()
        self.btn_preview.setIcon(get_svg_icon("eye", 15, "#63b3ed"))
        self.btn_preview.setToolTip("Inspect full resolution in right panel")
        self.btn_preview.setFixedSize(24, 24)
        self.btn_preview.setStyleSheet("""
            QPushButton {
                background: #171923;
                border: 1px solid #3d4a61;
                border-radius: 4px;
                padding: 1px;
            }
            QPushButton:hover {
                background: #2b6cb0;
                border-color: #63b3ed;
            }
        """)
        self.btn_preview.clicked.connect(lambda: self.preview_requested.emit(self.photo))

        header.addWidget(self.checkbox)
        header.addWidget(lbl_time)
        header.addStretch()
        header.addWidget(self.btn_preview)
        layout.addLayout(header)

        # Image Thumbnail (Clickable to trigger preview)
        self.img_label = QLabel()
        self.img_label.setFixedHeight(240)
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet("background: #11141c; border-radius: 4px;")
        self.img_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.img_label.setToolTip("Click to inspect in right preview panel")
        self.img_label.mousePressEvent = lambda e: self.preview_requested.emit(self.photo)

        if os.path.exists(self.photo.path):
            pixmap = QPixmap(self.photo.path)
            scaled = pixmap.scaled(
                214, 240,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.img_label.setPixmap(scaled)
        layout.addWidget(self.img_label)

        # Metrics Bar: Quality & Scene ID
        metrics = QHBoxLayout()
        quality_pct = int(self.photo.quality_score * 100)
        lbl_quality = QLabel(f"Quality: {quality_pct}%")
        lbl_quality.setStyleSheet("color: #68d391; font-weight: bold; font-size: 11px;")

        lbl_scene = QLabel(f"Scene #{self.photo.scene_id}")
        lbl_scene.setStyleSheet("color: #cbd5e0; font-size: 11px;")

        metrics.addWidget(lbl_quality)
        metrics.addStretch()
        metrics.addWidget(lbl_scene)
        layout.addLayout(metrics)

        # Action Buttons: Compare Slot A / Slot B (with SVG Icons)
        actions = QHBoxLayout()
        actions.setSpacing(6)

        btn_a = QPushButton(" Slot A")
        btn_a.setIcon(get_svg_icon("slot-a", 13, "#ecc94b"))
        btn_a.setFixedHeight(24)
        btn_a.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                padding: 2px 6px;
                background: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                color: #e2e8f0;
            }
            QPushButton:hover {
                background: #3182ce;
                border-color: #63b3ed;
                color: white;
            }
        """)
        btn_a.clicked.connect(lambda: self.set_compare_a.emit(self.photo.path))

        btn_b = QPushButton(" Slot B")
        btn_b.setIcon(get_svg_icon("slot-b", 13, "#ecc94b"))
        btn_b.setFixedHeight(24)
        btn_b.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                padding: 2px 6px;
                background: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                color: #e2e8f0;
            }
            QPushButton:hover {
                background: #3182ce;
                border-color: #63b3ed;
                color: white;
            }
        """)
        btn_b.clicked.connect(lambda: self.set_compare_b.emit(self.photo.path))

        actions.addWidget(btn_a)
        actions.addWidget(btn_b)
        layout.addLayout(actions)

    def _on_toggled(self, checked: bool):
        self.is_selected = checked
        if checked:
            self.setStyleSheet("""
                PhotoCard {
                    background-color: #232a3b;
                    border: 2px solid #3d4a61;
                    border-radius: 8px;
                }
                PhotoCard:hover {
                    border: 2px solid #63b3ed;
                    background-color: #2c364c;
                }
            """)
        else:
            self.setStyleSheet("""
                PhotoCard {
                    background-color: #171923;
                    border: 2px dashed #4a5568;
                    border-radius: 8px;
                    opacity: 0.5;
                }
            """)
        self.toggled.emit(self.photo.path, checked)

    def set_checked(self, checked: bool):
        self.checkbox.setChecked(checked)


class PhotoInspectorPanel(QFrame):
    """Right-hand docked inspector panel showing full high-res preview and detailed frame metadata."""

    set_compare_a = pyqtSignal(str)
    set_compare_b = pyqtSignal(str)
    selection_toggled = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_photo: Optional[SelectedPhoto] = None
        self._init_ui()

    def _init_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(320)
        self.setStyleSheet("""
            PhotoInspectorPanel {
                background-color: #1a202c;
                border-left: 2px solid #2d3748;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header bar with SVG icons
        header = QHBoxLayout()
        header.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap("eye", 18, "#63b3ed"))
        title_lbl = QLabel("Frame Inspector")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #63b3ed;")

        self.btn_copy_path = QPushButton()
        self.btn_copy_path.setIcon(get_svg_icon("copy", 14, "#a0aec0"))
        self.btn_copy_path.setToolTip("Copy photo file path to clipboard")
        self.btn_copy_path.setFixedSize(26, 26)
        self.btn_copy_path.setStyleSheet("""
            QPushButton { background: #2d3748; border-radius: 4px; border: 1px solid #4a5568; }
            QPushButton:hover { background: #4a5568; border-color: #63b3ed; }
        """)
        self.btn_copy_path.clicked.connect(self._copy_path)

        self.btn_open_ext = QPushButton()
        self.btn_open_ext.setIcon(get_svg_icon("external-link", 14, "#a0aec0"))
        self.btn_open_ext.setToolTip("Open in default system photo viewer")
        self.btn_open_ext.setFixedSize(26, 26)
        self.btn_open_ext.setStyleSheet("""
            QPushButton { background: #2d3748; border-radius: 4px; border: 1px solid #4a5568; }
            QPushButton:hover { background: #4a5568; border-color: #63b3ed; }
        """)
        self.btn_open_ext.clicked.connect(self._open_in_external_viewer)

        header.addWidget(icon_lbl)
        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(self.btn_copy_path)
        header.addWidget(self.btn_open_ext)
        layout.addLayout(header)

        # Large high-resolution image preview container
        self.img_preview = QLabel("Select any photograph to inspect")
        self.img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_preview.setStyleSheet("""
            background: #11141c;
            border: 1px solid #2d3748;
            border-radius: 8px;
            color: #718096;
            font-size: 13px;
        """)
        self.img_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.img_preview, stretch=4)

        # Details / Metrics card
        metrics_box = QFrame()
        metrics_box.setStyleSheet("""
            QFrame {
                background: #232a3b;
                border: 1px solid #2d3748;
                border-radius: 6px;
            }
        """)
        m_layout = QGridLayout(metrics_box)
        m_layout.setContentsMargins(12, 10, 12, 10)
        m_layout.setSpacing(8)

        lbl_hdr_time = QLabel("Timestamp:")
        lbl_hdr_time.setStyleSheet("color: #a0aec0; font-size: 11px;")
        self.lbl_time = QLabel("—")
        self.lbl_time.setStyleSheet("font-weight: bold; color: #e2e8f0; font-size: 12px;")

        lbl_hdr_dim = QLabel("Dimensions:")
        lbl_hdr_dim.setStyleSheet("color: #a0aec0; font-size: 11px;")
        self.lbl_dim = QLabel("—")
        self.lbl_dim.setStyleSheet("color: #cbd5e0; font-size: 12px;")

        lbl_hdr_q = QLabel("Quality Score:")
        lbl_hdr_q.setStyleSheet("color: #a0aec0; font-size: 11px;")
        self.lbl_quality = QLabel("—")
        self.lbl_quality.setStyleSheet("font-weight: bold; color: #68d391; font-size: 12px;")

        lbl_hdr_nov = QLabel("Visual Novelty:")
        lbl_hdr_nov.setStyleSheet("color: #a0aec0; font-size: 11px;")
        self.lbl_novelty = QLabel("—")
        self.lbl_novelty.setStyleSheet("color: #63b3ed; font-size: 12px;")

        lbl_hdr_sc = QLabel("Scene Cut #:")
        lbl_hdr_sc.setStyleSheet("color: #a0aec0; font-size: 11px;")
        self.lbl_scene = QLabel("—")
        self.lbl_scene.setStyleSheet("color: #ecc94b; font-size: 12px;")

        m_layout.addWidget(lbl_hdr_time, 0, 0)
        m_layout.addWidget(self.lbl_time, 0, 1)
        m_layout.addWidget(lbl_hdr_dim, 1, 0)
        m_layout.addWidget(self.lbl_dim, 1, 1)
        m_layout.addWidget(lbl_hdr_q, 2, 0)
        m_layout.addWidget(self.lbl_quality, 2, 1)
        m_layout.addWidget(lbl_hdr_nov, 3, 0)
        m_layout.addWidget(self.lbl_novelty, 3, 1)
        m_layout.addWidget(lbl_hdr_sc, 4, 0)
        m_layout.addWidget(self.lbl_scene, 4, 1)

        layout.addWidget(metrics_box, stretch=1)

        # Quick action buttons for the inspected frame
        actions_box = QHBoxLayout()
        actions_box.setSpacing(8)

        self.btn_slot_a = QPushButton(" Send to Slot A")
        self.btn_slot_a.setIcon(get_svg_icon("slot-a", 14, "#ecc94b"))
        self.btn_slot_a.setStyleSheet("""
            QPushButton {
                background: #2d3748;
                border: 1px solid #4a5568;
                font-weight: 600;
                padding: 6px 12px;
                border-radius: 4px;
                color: #e2e8f0;
            }
            QPushButton:hover {
                background: #3182ce;
                border-color: #63b3ed;
                color: white;
            }
        """)
        self.btn_slot_a.clicked.connect(self._on_slot_a)

        self.btn_slot_b = QPushButton(" Send to Slot B")
        self.btn_slot_b.setIcon(get_svg_icon("slot-b", 14, "#ecc94b"))
        self.btn_slot_b.setStyleSheet("""
            QPushButton {
                background: #2d3748;
                border: 1px solid #4a5568;
                font-weight: 600;
                padding: 6px 12px;
                border-radius: 4px;
                color: #e2e8f0;
            }
            QPushButton:hover {
                background: #3182ce;
                border-color: #63b3ed;
                color: white;
            }
        """)
        self.btn_slot_b.clicked.connect(self._on_slot_b)

        actions_box.addWidget(self.btn_slot_a)
        actions_box.addWidget(self.btn_slot_b)
        layout.addLayout(actions_box)

    def inspect_photo(self, photo: SelectedPhoto):
        """Display full details of the given photo in the inspector."""
        self.current_photo = photo
        if not photo or not os.path.exists(photo.path):
            self.img_preview.setText("Image not available")
            return

        pixmap = QPixmap(photo.path)
        scaled = pixmap.scaled(
            420, 500,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.img_preview.setPixmap(scaled)

        # Update metadata labels
        time_fmt = f"{photo.timestamp_sec:.3f}s (Frame #{photo.frame_index})"
        self.lbl_time.setText(time_fmt)

        w, h = photo.dimensions
        ratio_str = "Portrait" if h > w else "Landscape" if w > h else "Square"
        self.lbl_dim.setText(f"{w} × {h} px ({ratio_str})")

        quality_pct = int(photo.quality_score * 100)
        self.lbl_quality.setText(f"{quality_pct}% (Score: {photo.quality_score:.3f})")

        self.lbl_novelty.setText(f"{photo.novelty_score:.4f}")
        self.lbl_scene.setText(f"Shot Segment #{photo.scene_id}")

    def _on_slot_a(self):
        if self.current_photo:
            self.set_compare_a.emit(self.current_photo.path)

    def _on_slot_b(self):
        if self.current_photo:
            self.set_compare_b.emit(self.current_photo.path)

    def _copy_path(self):
        if self.current_photo:
            clipboard = QApplication.clipboard()
            clipboard.setText(os.path.abspath(self.current_photo.path))

    def _open_in_external_viewer(self):
        if self.current_photo and os.path.exists(self.current_photo.path):
            abs_path = os.path.abspath(self.current_photo.path)
            if sys.platform == "win32":
                os.startfile(abs_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", abs_path])
            else:
                subprocess.Popen(["xdg-open", abs_path])


class ComparisonPanel(QWidget):
    """Side-by-side comparison panel to inspect similar frames and pick the best one."""

    selection_changed = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.photos_map: Dict[str, SelectedPhoto] = {}
        self.path_a: Optional[str] = None
        self.path_b: Optional[str] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Quick resolution controls
        action_bar = QHBoxLayout()
        icon_cmp = QLabel()
        icon_cmp.setPixmap(get_svg_pixmap("compare", 20, "#63b3ed"))
        lbl_title = QLabel("Side-by-Side Candidate Comparator")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #63b3ed;")

        btn_keep_a = QPushButton(" Keep Only A")
        btn_keep_a.setIcon(get_svg_icon("check", 14, "#ffffff"))
        btn_keep_a.setStyleSheet("""
            QPushButton { background: #2b6cb0; font-weight: bold; padding: 6px 14px; border-radius: 4px; }
            QPushButton:hover { background: #3182ce; }
        """)
        btn_keep_a.clicked.connect(self._keep_only_a)

        btn_keep_b = QPushButton(" Keep Only B")
        btn_keep_b.setIcon(get_svg_icon("check", 14, "#ffffff"))
        btn_keep_b.setStyleSheet("""
            QPushButton { background: #2b6cb0; font-weight: bold; padding: 6px 14px; border-radius: 4px; }
            QPushButton:hover { background: #3182ce; }
        """)
        btn_keep_b.clicked.connect(self._keep_only_b)

        btn_keep_both = QPushButton("Keep Both")
        btn_keep_both.setStyleSheet("""
            QPushButton { background: #2d3748; padding: 6px 12px; border-radius: 4px; }
            QPushButton:hover { background: #4a5568; }
        """)
        btn_keep_both.clicked.connect(self._keep_both)

        action_bar.addWidget(icon_cmp)
        action_bar.addWidget(lbl_title)
        action_bar.addStretch()
        action_bar.addWidget(btn_keep_a)
        action_bar.addWidget(btn_keep_b)
        action_bar.addWidget(btn_keep_both)
        layout.addLayout(action_bar)

        # Side by Side split view
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left slot (Image A)
        self.box_a = QGroupBox("Candidate A")
        box_a_layout = QVBoxLayout(self.box_a)
        self.combo_a = QComboBox()
        self.combo_a.currentIndexChanged.connect(self._on_combo_a_changed)
        self.img_a = QLabel("No image selected for Slot A")
        self.img_a.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_a.setStyleSheet("background: #171923; border-radius: 6px;")
        self.img_a.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.info_a = QLabel("")
        self.info_a.setStyleSheet("color: #cbd5e0; font-size: 12px;")
        box_a_layout.addWidget(self.combo_a)
        box_a_layout.addWidget(self.img_a, stretch=1)
        box_a_layout.addWidget(self.info_a)
        splitter.addWidget(self.box_a)

        # Right slot (Image B)
        self.box_b = QGroupBox("Candidate B")
        box_b_layout = QVBoxLayout(self.box_b)
        self.combo_b = QComboBox()
        self.combo_b.currentIndexChanged.connect(self._on_combo_b_changed)
        self.img_b = QLabel("No image selected for Slot B")
        self.img_b.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_b.setStyleSheet("background: #171923; border-radius: 6px;")
        self.img_b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.info_b = QLabel("")
        self.info_b.setStyleSheet("color: #cbd5e0; font-size: 12px;")
        box_b_layout.addWidget(self.combo_b)
        box_b_layout.addWidget(self.img_b, stretch=1)
        box_b_layout.addWidget(self.info_b)
        splitter.addWidget(self.box_b)

        layout.addWidget(splitter, stretch=1)

    def set_photos(self, photos: List[SelectedPhoto]):
        self.photos_map = {p.path: p for p in photos}
        self.combo_a.blockSignals(True)
        self.combo_b.blockSignals(True)
        self.combo_a.clear()
        self.combo_b.clear()

        for p in photos:
            label = f"#{p.frame_index} ({p.timestamp_sec:.2f}s) - Quality {int(p.quality_score * 100)}%"
            self.combo_a.addItem(label, p.path)
            self.combo_b.addItem(label, p.path)

        self.combo_a.blockSignals(False)
        self.combo_b.blockSignals(False)

        if len(photos) > 0:
            self.set_slot_a(photos[0].path)
        if len(photos) > 1:
            self.set_slot_b(photos[1].path)

    def set_slot_a(self, path: str):
        self.path_a = path
        index = self.combo_a.findData(path)
        if index >= 0:
            self.combo_a.setCurrentIndex(index)
        self._render_slot(path, self.img_a, self.info_a, "Candidate A")

    def set_slot_b(self, path: str):
        self.path_b = path
        index = self.combo_b.findData(path)
        if index >= 0:
            self.combo_b.setCurrentIndex(index)
        self._render_slot(path, self.img_b, self.info_b, "Candidate B")

    def _render_slot(self, path: str, img_label: QLabel, info_label: QLabel, title: str):
        if not path or not os.path.exists(path):
            img_label.setText("Image not found")
            info_label.setText("")
            return

        pixmap = QPixmap(path)
        scaled = pixmap.scaled(
            480, 560,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        img_label.setPixmap(scaled)

        photo = self.photos_map.get(path)
        if photo:
            info = (
                f"<b>Timestamp:</b> {photo.timestamp_sec:.3f}s &nbsp;|&nbsp; "
                f"<b>Dimensions:</b> {photo.dimensions[0]}x{photo.dimensions[1]} &nbsp;|&nbsp; "
                f"<b>Quality Score:</b> <span style='color:#68d391;'>{photo.quality_score:.2f}</span> &nbsp;|&nbsp; "
                f"<b>Novelty:</b> {photo.novelty_score:.3f}"
            )
            info_label.setText(info)

    def _on_combo_a_changed(self, idx: int):
        path = self.combo_a.currentData()
        if path:
            self.set_slot_a(path)

    def _on_combo_b_changed(self, idx: int):
        path = self.combo_b.currentData()
        if path:
            self.set_slot_b(path)

    def _keep_only_a(self):
        if self.path_a:
            self.selection_changed.emit(self.path_a, True)
        if self.path_b:
            self.selection_changed.emit(self.path_b, False)

    def _keep_only_b(self):
        if self.path_b:
            self.selection_changed.emit(self.path_b, True)
        if self.path_a:
            self.selection_changed.emit(self.path_a, False)

    def _keep_both(self):
        if self.path_a:
            self.selection_changed.emit(self.path_a, True)
        if self.path_b:
            self.selection_changed.emit(self.path_b, True)


class CentralCanvas(QStackedWidget):
    """Central view area holding the Gallery Grid with Live Right-Side Inspector and the Comparison Inspector."""

    selection_changed = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards: Dict[str, PhotoCard] = {}
        self._init_ui()

    def _init_ui(self):
        # View 0: Gallery Grid Splitter (Scrollable Cards on Left, Inspector on Right)
        self.gallery_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.gallery_splitter.setStyleSheet("""
            QSplitter::handle {
                background: #2d3748;
                width: 3px;
            }
            QSplitter::handle:hover {
                background: #63b3ed;
            }
        """)

        # Left: Scrollable Gallery Grid
        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setStyleSheet("QScrollArea { border: none; background: #171923; }")

        self.gallery_container = QWidget()
        self.gallery_container.setStyleSheet("background: #171923;")
        self.grid_layout = QGridLayout(self.gallery_container)
        self.grid_layout.setContentsMargins(16, 16, 16, 16)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.gallery_scroll.setWidget(self.gallery_container)
        self.gallery_splitter.addWidget(self.gallery_scroll)

        # Right: Live Photo Inspector Panel (fills the previously empty right side)
        self.inspector = PhotoInspectorPanel()
        self.inspector.set_compare_a.connect(self._set_compare_a)
        self.inspector.set_compare_b.connect(self._set_compare_b)
        self.gallery_splitter.addWidget(self.inspector)

        # Allocate 70% space to grid, 30% to inspector
        self.gallery_splitter.setStretchFactor(0, 3)
        self.gallery_splitter.setStretchFactor(1, 1)

        self.addWidget(self.gallery_splitter)

        # View 1: A/B Comparison View
        self.compare_view = ComparisonPanel()
        self.compare_view.selection_changed.connect(self._on_compare_selection_changed)
        self.addWidget(self.compare_view)

    def set_view_mode(self, mode: int):
        """Switch between 0 (Gallery) and 1 (A/B Compare)."""
        self.setCurrentIndex(mode)

    def populate_photos(self, photos: List[SelectedPhoto]):
        """Populate gallery and comparator with newly extracted photos."""
        # Clear existing
        self.cards.clear()
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        cols = 3  # Optimized column count to fit comfortably alongside the right inspector
        for idx, photo in enumerate(photos):
            card = PhotoCard(photo)
            card.toggled.connect(self._on_card_toggled)
            card.set_compare_a.connect(self._set_compare_a)
            card.set_compare_b.connect(self._set_compare_b)
            card.preview_requested.connect(self.inspector.inspect_photo)

            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(card, row, col)
            self.cards[photo.path] = card

        self.compare_view.set_photos(photos)

        # Pre-load the first photo into the inspector panel
        if photos:
            self.inspector.inspect_photo(photos[0])

    def _on_card_toggled(self, path: str, checked: bool):
        self.selection_changed.emit(path, checked)

    def _on_compare_selection_changed(self, path: str, checked: bool):
        card = self.cards.get(path)
        if card:
            card.set_checked(checked)
        self.selection_changed.emit(path, checked)

    def _set_compare_a(self, path: str):
        self.compare_view.set_slot_a(path)
        self.setCurrentIndex(1)  # Switch to comparison view

    def _set_compare_b(self, path: str):
        self.compare_view.set_slot_b(path)
        self.setCurrentIndex(1)  # Switch to comparison view

    def set_all_selected(self, selected: bool):
        for card in self.cards.values():
            card.set_checked(selected)

    def invert_selection(self):
        for card in self.cards.values():
            card.set_checked(not card.is_selected)

    def filter_by_sharpness(self, min_sharpness: float):
        for card in self.cards.values():
            should_show = (card.photo.quality_score * 100.0) >= min_sharpness
            card.setVisible(should_show)

    def get_selected_photos(self) -> List[str]:
        return [path for path, card in self.cards.items() if card.is_selected]
