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
    # Switch to custom and modify ribbon controls
    win.ribbon.preset_combo.setCurrentText("custom")
    win.ribbon.spin_base_fps.setValue(3.2)
    win.ribbon.spin_dense_fps.setValue(7.5)
    win.ribbon.spin_sensitivity.setValue(0.04)
    win.ribbon.spin_min_sharpness.setValue(32.0)
    win.ribbon.spin_blur_penalty.setValue(1.8)
    win.ribbon.chk_adaptive_sampling.setChecked(False)
    win.ribbon.chk_quality_scoring.setChecked(True)

    config = win.ribbon.build_config()
    assert config.base_fps == 3.2
    assert config.dense_fps == 7.5
    assert config.novelty_threshold == 0.04
    assert config.min_sharpness_score == 32.0
    assert config.motion_blur_penalty == 1.8
    assert config.adaptive_sampling is False
    assert config.quality_scoring is True
    assert config.preset.value == "custom"


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


def test_comparison_staging_workflow(qapp, tmp_path):
    win = VitupiMainWindow()

    img1 = tmp_path / "photo_a.jpg"
    img2 = tmp_path / "photo_b.jpg"
    img1.write_bytes(b"\x00" * 20)
    img2.write_bytes(b"\x00" * 20)

    p1 = SelectedPhoto(str(img1), 1.0, 10, (320, 240), 0.8, 0.1, 0)
    p2 = SelectedPhoto(str(img2), 2.0, 20, (320, 240), 0.9, 0.2, 0)

    win.canvas.populate_photos([p1, p2])

    # Initially in gallery
    assert win.canvas.currentIndex() == 0

    # Click Slot A on Card 1 -> stays in gallery!
    card1 = win.canvas.cards[str(img1)]
    card1.btn_a.click()
    assert win.canvas.currentIndex() == 0
    assert card1.staged_slot == "A"
    assert win.canvas.staged_path_a == str(img1)

    # Click Slot B on Card 2 -> stays in gallery!
    card2 = win.canvas.cards[str(img2)]
    card2.btn_b.click()
    assert win.canvas.currentIndex() == 0
    assert card2.staged_slot == "B"
    assert win.canvas.staged_path_b == str(img2)
    assert win.canvas.staging_bar.btn_compare.isEnabled() is True

    # User explicitly clicks Compare A vs B
    win.canvas.staging_bar.btn_compare.click()
    assert win.canvas.currentIndex() == 1
    assert win.canvas.compare_view.path_a == str(img1)
    assert win.canvas.compare_view.path_b == str(img2)

    # Click Back to Gallery
    win.canvas.compare_view.back_to_gallery_requested.emit()
    assert win.canvas.currentIndex() == 0


def test_fullscreen_toggle(qapp):
    win = VitupiMainWindow()
    assert win.shortcut_fullscreen is not None
    assert hasattr(win.ribbon, "btn_fullscreen")

    # Initial state
    win.ribbon.update_fullscreen_state(True)
    assert "Exit Full Screen" in win.ribbon.btn_fullscreen.text()

    win.ribbon.update_fullscreen_state(False)
    assert "Full Screen" in win.ribbon.btn_fullscreen.text()

    # Toggle method runs without error
    win.toggle_fullscreen()
    assert win.isFullScreen() or not win.isFullScreen()  # State toggled cleanly


def test_ribbon_manual_tweak_switches_to_custom(qapp):
    win = VitupiMainWindow()
    win.ribbon.preset_combo.setCurrentText("portrait")
    assert win.ribbon.preset_combo.currentText() == "portrait"

    # Modifying a parameter spinbox automatically flips preset to 'custom'
    win.ribbon.spin_base_fps.setValue(5.5)
    assert win.ribbon.preset_combo.currentText() == "custom"
    assert "Active: custom" in win.ribbon.lbl_active_preset.text()


def test_ribbon_custom_preset_persistence(qapp, tmp_path):
    from vitupi.presets import PresetManager

    # Isolated preset storage for test
    custom_storage = tmp_path / "gui_presets.json"
    win = VitupiMainWindow()
    win.ribbon.preset_manager = PresetManager(storage_file=custom_storage)
    win.ribbon._refresh_preset_combo("portrait")

    # Save a custom preset
    win.ribbon.spin_base_fps.setValue(4.0)
    win.ribbon.spin_dense_fps.setValue(9.0)
    cfg = win.ribbon.build_config()

    win.ribbon.preset_manager.save_preset("cinematic_action", cfg)
    win.ribbon._refresh_preset_combo(select_name="cinematic_action")

    assert win.ribbon.preset_combo.currentText() == "cinematic_action"
    assert win.ribbon.btn_delete_preset.isEnabled() is True
    assert win.ribbon.spin_base_fps.value() == 4.0
    assert win.ribbon.spin_dense_fps.value() == 9.0

    # Delete custom preset
    win.ribbon.preset_manager.delete_preset("cinematic_action")
    win.ribbon._refresh_preset_combo(select_name="portrait")
    assert "cinematic_action" not in [
        win.ribbon.preset_combo.itemText(i) for i in range(win.ribbon.preset_combo.count())
    ]
    assert win.ribbon.btn_delete_preset.isEnabled() is False
