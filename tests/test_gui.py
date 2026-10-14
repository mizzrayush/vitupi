"""
Unit tests for the Vitupi PyQt6 GUI application.
"""

import os
import pytest

# Ensure headless offscreen platform for CI/headless environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from vitupi.gui.icons import get_svg_icon, get_svg_pixmap
from vitupi.gui.main_window import VitupiMainWindow
from vitupi.models import SelectedPhoto


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_svg_icon_generation(qapp):
    icon_eye = get_svg_icon("eye", 20, "#63b3ed")
    assert not icon_eye.isNull()
    pixmap = get_svg_pixmap("compare", 24, "#ffffff")
    assert not pixmap.isNull()
    assert pixmap.width() == 24


def test_main_window_initialization(qapp):
    win = VitupiMainWindow()
    assert win.windowTitle().startswith("Vitupi (V2P)")
    assert win.ribbon.count() == 4
    assert win.canvas.count() == 2
    assert win.canvas.currentIndex() == 0  # Gallery is default view
    assert win.canvas.inspector is not None


def test_main_window_with_initial_video(qapp, tmp_path):
    dummy_video = tmp_path / "sample.mp4"
    dummy_video.write_bytes(b"\x00" * 100)

    win = VitupiMainWindow(initial_video=str(dummy_video))
    assert win.ribbon.video_path_edit.text() == str(dummy_video.resolve())


def test_ribbon_config_building(qapp):
    win = VitupiMainWindow()
    # Modify some ribbon controls
    win.ribbon.spin_base_fps.setValue(3.2)
    win.ribbon.spin_dense_fps.setValue(7.5)
    win.ribbon.spin_sensitivity.setValue(0.04)
    win.ribbon.spin_min_sharpness.setValue(32.0)
    win.ribbon.preset_combo.setCurrentText("portrait")

    config = win.ribbon.build_config()
    assert config.base_fps == 3.2
    assert config.dense_fps == 7.5
    assert config.novelty_threshold == 0.04
    assert config.min_sharpness_score == 32.0
    assert config.preset.value == "portrait"


def test_canvas_populate_and_inspector(qapp, tmp_path):
    win = VitupiMainWindow()

    # Create dummy images
    img1 = tmp_path / "frame_1.jpg"
    img2 = tmp_path / "frame_2.jpg"
    img1.write_bytes(b"\x00" * 50)
    img2.write_bytes(b"\x00" * 50)

    p1 = SelectedPhoto(
        path=str(img1),
        timestamp_sec=0.42,
        frame_index=10,
        dimensions=(640, 480),
        quality_score=0.88,
        novelty_score=0.15,
        scene_id=0,
    )
    p2 = SelectedPhoto(
        path=str(img2),
        timestamp_sec=0.84,
        frame_index=20,
        dimensions=(640, 480),
        quality_score=0.92,
        novelty_score=0.22,
        scene_id=0,
    )

    win.canvas.populate_photos([p1, p2])
    assert len(win.canvas.cards) == 2
    assert win.canvas.get_selected_photos() == [str(img1), str(img2)]

    # Verify inspector pre-loaded photo 1
    assert win.canvas.inspector.current_photo == p1
    assert "0.420s" in win.canvas.inspector.lbl_time.text()

    # Click preview icon on card 2
    card2 = win.canvas.cards[str(img2)]
    assert card2.btn_preview is not None
    card2.btn_preview.click()
    assert win.canvas.inspector.current_photo == p2
    assert "0.840s" in win.canvas.inspector.lbl_time.text()

    # Switch view to Compare
    win.canvas.set_view_mode(1)
    assert win.canvas.currentIndex() == 1

    # Test selection manipulation
    win.canvas.set_all_selected(False)
    assert len(win.canvas.get_selected_photos()) == 0

    win.canvas.set_all_selected(True)
    assert len(win.canvas.get_selected_photos()) == 2
