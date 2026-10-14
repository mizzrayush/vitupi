"""
Central Interactive Canvas for Vitupi GUI.
Supports Gallery Grid View and Side-by-Side A/B Image Comparison.
"""

import os
from typing import Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPixmap
from PyQt6.QtWidgets import (
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

from vitupi.models import SelectedPhoto


class PhotoCard(QFrame):
    """Card widget representing an individual extracted photograph."""

    toggled = pyqtSignal(str, bool)  # path, is_selected
    set_compare_a = pyqtSignal(str)   # path
    set_compare_b = pyqtSignal(str)   # path

    def __init__(self, photo: SelectedPhoto, parent=None):
        super().__init__(parent)
        self.photo = photo
        self.is_selected = True
        self._init_ui()

    def _init_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedWidth(240)
        self.setStyleSheet("""
            PhotoCard {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 8px;
            }
            PhotoCard:hover {
                border: 2px solid #63b3ed;
                background-color: #323f54;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header: Checkbox + Timestamp Badge
        header = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.toggled.connect(self._on_toggled)

        time_str = f"{self.photo.timestamp_sec:.2f}s"
        lbl_time = QLabel(time_str)
        lbl_time.setStyleSheet("""
            background: #1a202c;
            color: #e2e8f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
        """)

        header.addWidget(self.checkbox)
        header.addStretch()
        header.addWidget(lbl_time)
        layout.addLayout(header)

        # Image Thumbnail
        self.img_label = QLabel()
        self.img_label.setFixedHeight(260)
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet("background: #171923; border-radius: 4px;")
        if os.path.exists(self.photo.path):
            pixmap = QPixmap(self.photo.path)
            scaled = pixmap.scaled(
                224, 260,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.img_label.setPixmap(scaled)
        layout.addWidget(self.img_label)

        # Metrics Bar: Sharpness & Novelty
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

        # Action Buttons: Compare A / B
        actions = QHBoxLayout()
        btn_a = QPushButton("⚖️ Slot A")
        btn_a.setFixedHeight(24)
        btn_a.setStyleSheet("font-size: 10px; padding: 2px 4px; background: #4a5568;")
        btn_a.clicked.connect(lambda: self.set_compare_a.emit(self.photo.path))

        btn_b = QPushButton("⚖️ Slot B")
        btn_b.setFixedHeight(24)
        btn_b.setStyleSheet("font-size: 10px; padding: 2px 4px; background: #4a5568;")
        btn_b.clicked.connect(lambda: self.set_compare_b.emit(self.photo.path))

        actions.addWidget(btn_a)
        actions.addWidget(btn_b)
        layout.addLayout(actions)

    def _on_toggled(self, checked: bool):
        self.is_selected = checked
        if checked:
            self.setStyleSheet("""
                PhotoCard {
                    background-color: #2d3748;
                    border: 2px solid #4a5568;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                PhotoCard {
                    background-color: #1a202c;
                    border: 2px dashed #4a5568;
                    border-radius: 8px;
                    opacity: 0.5;
                }
            """)
        self.toggled.emit(self.photo.path, checked)

    def set_checked(self, checked: bool):
        self.checkbox.setChecked(checked)


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
        lbl_title = QLabel("🔍 Side-by-Side Candidate Comparator")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #63b3ed;")

        btn_keep_a = QPushButton("✅ Keep Only A (Deselect B)")
        btn_keep_a.setStyleSheet("background: #2b6cb0; font-weight: bold; padding: 6px 12px;")
        btn_keep_a.clicked.connect(self._keep_only_a)

        btn_keep_b = QPushButton("✅ Keep Only B (Deselect A)")
        btn_keep_b.setStyleSheet("background: #2b6cb0; font-weight: bold; padding: 6px 12px;")
        btn_keep_b.clicked.connect(self._keep_only_b)

        btn_keep_both = QPushButton("Keep Both")
        btn_keep_both.clicked.connect(self._keep_both)

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
    """Central view area holding the Gallery Grid and the Comparison Inspector."""

    selection_changed = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards: Dict[str, PhotoCard] = {}
        self._init_ui()

    def _init_ui(self):
        # View 0: Scrollable Gallery Grid
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
        self.addWidget(self.gallery_scroll)

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

        cols = 4
        for idx, photo in enumerate(photos):
            card = PhotoCard(photo)
            card.toggled.connect(self._on_card_toggled)
            card.set_compare_a.connect(self._set_compare_a)
            card.set_compare_b.connect(self._set_compare_b)

            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(card, row, col)
            self.cards[photo.path] = card

        self.compare_view.set_photos(photos)

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
