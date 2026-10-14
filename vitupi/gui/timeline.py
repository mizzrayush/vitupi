"""
Chronological Video Timeline Scrubber for Vitupi GUI.
Displays video duration ruler, detected scene segment bands, candidate photograph markers,
and interactive playhead scrubbing with synchronized gallery navigation.
"""

from typing import List, Optional, Tuple
from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QLinearGradient, QMouseEvent, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QToolTip, QWidget

from vitupi.models import SceneBoundary, SelectedPhoto


class VideoTimelineWidget(QWidget):
    """Interactive hardware-painted chronological video scrubber."""

    photo_selected = pyqtSignal(str)   # Emits photo file path
    seek_requested = pyqtSignal(float)  # Emits timestamp in seconds

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(72)
        self.setMinimumWidth(400)
        self.setMouseTracking(True)

        self._duration: float = 0.0
        self._current_time: float = 0.0
        self._scenes: List[SceneBoundary] = []
        self._photos: List[SelectedPhoto] = []
        self._selected_photo_path: Optional[str] = None
        self._hovered_photo: Optional[SelectedPhoto] = None
        self._is_dragging: bool = False

        # Visual layout constants
        self._margin_left = 48
        self._margin_right = 48
        self._ruler_height = 20
        self._track_height = 36
        self._track_top = 24

        self.setStyleSheet("background-color: transparent;")

    def set_duration(self, duration_sec: float):
        """Set the total video duration in seconds."""
        self._duration = max(0.0, duration_sec)
        self.update()

    def set_scenes(self, scenes: List[SceneBoundary]):
        """Set detected scene boundaries to render segment bands."""
        self._scenes = list(scenes)
        self.update()

    def set_photos(self, photos: List[SelectedPhoto]):
        """Populate extracted photo pins along the timeline."""
        self._photos = list(photos)
        self._hovered_photo = None
        self.update()

    def select_photo(self, photo_path: str):
        """Highlight marker corresponding to the given photo path."""
        self._selected_photo_path = photo_path
        # Also seek playhead to this photo's timestamp if found
        for p in self._photos:
            if p.path == photo_path:
                self._current_time = p.timestamp_sec
                break
        self.update()

    def set_current_time(self, timestamp_sec: float):
        """Update playhead position."""
        self._current_time = max(0.0, min(self._duration, timestamp_sec)) if self._duration > 0 else 0.0
        self.update()

    def clear(self):
        """Reset timeline state."""
        self._duration = 0.0
        self._current_time = 0.0
        self._scenes.clear()
        self._photos.clear()
        self._selected_photo_path = None
        self._hovered_photo = None
        self.update()

    def _track_width(self) -> float:
        return max(1.0, float(self.width() - self._margin_left - self._margin_right))

    def _time_to_x(self, t: float) -> float:
        if self._duration <= 0:
            return float(self._margin_left)
        fraction = max(0.0, min(1.0, t / self._duration))
        return self._margin_left + (fraction * self._track_width())

    def _x_to_time(self, x: float) -> float:
        if self._duration <= 0:
            return 0.0
        fraction = (x - self._margin_left) / self._track_width()
        return max(0.0, min(self._duration, fraction * self._duration))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Background container
        bg_rect = QRectF(4, 4, w - 8, h - 8)
        painter.setPen(QPen(QColor("#2A303C"), 1))
        painter.setBrush(QBrush(QColor("#16181E")))
        painter.drawRoundedRect(bg_rect, 6, 6)

        track_rect = QRectF(self._margin_left, self._track_top, self._track_width(), self._track_height)

        # 2. Draw Scene segment bands if scenes exist, else dark track background
        if self._scenes and self._duration > 0:
            for i, scene in enumerate(self._scenes):
                x1 = self._time_to_x(scene.start_time_sec)
                x2 = self._time_to_x(scene.end_time_sec)
                scene_rect = QRectF(x1, self._track_top, max(1.0, x2 - x1), self._track_height)

                # Alternating elegant slate tones
                fill_color = QColor("#1D2330") if i % 2 == 0 else QColor("#222938")
                painter.fillRect(scene_rect, fill_color)

                # Scene divider line
                painter.setPen(QPen(QColor("#333C4E"), 1))
                painter.drawLine(QPointF(x2, self._track_top), QPointF(x2, self._track_top + self._track_height))
        else:
            painter.fillRect(track_rect, QColor("#1A1D24"))

        # Track border outline
        painter.setPen(QPen(QColor("#2E3846"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(track_rect, 3, 3)

        # 3. Time Ruler Ticks & Labels
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#718096"), 1))

        if self._duration > 0:
            # Determine suitable tick step (in seconds) based on track width
            tw = self._track_width()
            desired_ticks = max(3, int(tw / 80))
            raw_step = self._duration / desired_ticks
            # Snap step to standard intervals: 1, 2, 5, 10, 15, 30, 60, 120, 300, 600
            intervals = [1, 2, 5, 10, 15, 30, 60, 120, 300, 600]
            step = intervals[-1]
            for itv in intervals:
                if itv >= raw_step:
                    step = itv
                    break

            t = 0.0
            while t <= self._duration:
                x = self._time_to_x(t)
                painter.drawLine(QPointF(x, 8), QPointF(x, 15))

                mins = int(t // 60)
                secs = int(t % 60)
                time_str = f"{mins:02d}:{secs:02d}"
                painter.drawText(QRectF(x - 24, 6, 48, 14), Qt.AlignmentFlag.AlignCenter, time_str)
                t += step
        else:
            painter.drawText(QRectF(self._margin_left, 6, 120, 14), Qt.AlignmentFlag.AlignLeft, "00:00")

        # 4. Extracted Photo Pins / Markers
        for photo in self._photos:
            px = self._time_to_x(photo.timestamp_sec)
            py = self._track_top + (self._track_height / 2.0)
            is_selected = (self._selected_photo_path == photo.path)
            is_hovered = (self._hovered_photo == photo)

            # Marker color by composite quality
            if photo.quality_score >= 85:
                base_color = QColor("#00E5FF")  # Bright Cyan
            elif photo.quality_score >= 70:
                base_color = QColor("#3B82F6")  # Vivid Blue
            else:
                base_color = QColor("#F59E0B")  # Amber

            radius = 6.0 if (is_selected or is_hovered) else 4.5

            if is_selected:
                # Glowing selection halo
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(0, 229, 255, 70)))
                painter.drawEllipse(QPointF(px, py), radius + 4, radius + 4)

            # Outer ring
            painter.setPen(QPen(QColor("#FFFFFF") if (is_selected or is_hovered) else QColor("#111317"), 1.5))
            painter.setBrush(QBrush(base_color))
            painter.drawEllipse(QPointF(px, py), radius, radius)

        # 5. Playhead Scrubber Handle & Needle
        if self._duration > 0:
            cx = self._time_to_x(self._current_time)
            # Scrubber needle
            painter.setPen(QPen(QColor("#00E5FF"), 1.8))
            painter.drawLine(QPointF(cx, 16), QPointF(cx, self._track_top + self._track_height + 4))

            # Playhead triangle / diamond head
            head_path = QPainterPath()
            head_path.moveTo(cx - 5, 10)
            head_path.lineTo(cx + 5, 10)
            head_path.lineTo(cx, 18)
            head_path.closeSubpath()
            painter.setPen(QPen(QColor("#00B0FF"), 1))
            painter.setBrush(QBrush(QColor("#00E5FF")))
            painter.drawPath(head_path)

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicked on a photo marker
            clicked_photo = self._find_photo_at(event.position().x(), event.position().y())
            if clicked_photo:
                self.select_photo(clicked_photo.path)
                self.photo_selected.emit(clicked_photo.path)
                return

            # Otherwise, initiate scrubber drag
            self._is_dragging = True
            t = self._x_to_time(event.position().x())
            self.set_current_time(t)
            self.seek_requested.emit(t)

    def mouseMoveEvent(self, event: QMouseEvent):
        x = event.position().x()
        y = event.position().y()

        if self._is_dragging:
            t = self._x_to_time(x)
            self.set_current_time(t)
            self.seek_requested.emit(t)
            return

        # Handle hover tooltips on photo markers
        hovered = self._find_photo_at(x, y)
        if hovered != self._hovered_photo:
            self._hovered_photo = hovered
            self.update()

        if hovered:
            mins = int(hovered.timestamp_sec // 60)
            secs = hovered.timestamp_sec % 60
            tip = (
                f"Photo @ {mins:02d}:{secs:04.1f}\n"
                f"Quality Score: {hovered.quality_score:.1f} / 100\n"
                f"Selection: {hovered.selection_reason}\n"
                f"Scene: #{hovered.scene_id}"
            )
            QToolTip.showText(event.globalPosition().toPoint(), tip, self)
        else:
            QToolTip.hideText()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False

    def _find_photo_at(self, x: float, y: float, tolerance: float = 8.0) -> Optional[SelectedPhoto]:
        py = self._track_top + (self._track_height / 2.0)
        if abs(y - py) > tolerance * 2.5:
            return None

        for photo in self._photos:
            px = self._time_to_x(photo.timestamp_sec)
            if abs(x - px) <= tolerance:
                return photo
        return None
