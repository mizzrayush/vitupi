"""
Unit tests for preset persistence, custom preset creation, and management.
"""

import json
import pytest
from pathlib import Path

from vitupi.config import DomainPreset, ExtractionMode, VitupiConfig, get_preset_defaults
from vitupi.presets import PresetManager


def test_custom_domain_preset_enum():
    assert DomainPreset.CUSTOM.value == "custom"
    cfg = VitupiConfig(preset=DomainPreset.CUSTOM)
    assert cfg.preset == DomainPreset.CUSTOM
    # Verify reasonable defaults are provided for custom preset
    assert cfg.base_fps == 1.5
    assert cfg.dense_fps == 5.0
    assert cfg.flattery_filter is True


def test_config_serialization_round_trip():
    cfg = VitupiConfig(
        mode=ExtractionMode.EXHAUSTIVE,
        preset=DomainPreset.CUSTOM,
        custom_name="drone_cinematic",
        max_photos=250,
        base_fps=3.0,
        dense_fps=12.0,
        novelty_threshold=0.018,
        min_sharpness_score=30.0,
        motion_blur_penalty=2.2,
        flattery_filter=False,
        action_peak_detection=True,
    )

    data = cfg.to_dict()
    assert data["preset"] == "custom"
    assert data["custom_name"] == "drone_cinematic"
    assert data["base_fps"] == 3.0
    assert data["dense_fps"] == 12.0
    assert data["motion_blur_penalty"] == 2.2
    assert data["action_peak_detection"] is True

    # Reconstitute from dict
    reloaded = VitupiConfig.from_dict(data)
    assert reloaded.mode == ExtractionMode.EXHAUSTIVE
    assert reloaded.preset == DomainPreset.CUSTOM
    assert reloaded.custom_name == "drone_cinematic"
    assert reloaded.base_fps == 3.0
    assert reloaded.dense_fps == 12.0
    assert reloaded.motion_blur_penalty == 2.2


def test_preset_manager_save_and_load(tmp_path):
    storage_file = tmp_path / "test_presets.json"
    manager = PresetManager(storage_file=storage_file)

    # Initially only built-ins
    all_presets = manager.list_all_presets()
    assert "portrait" in all_presets
    assert "candid" in all_presets
    assert "custom" in all_presets

    # Create and save a custom preset
    custom_cfg = VitupiConfig(
        preset=DomainPreset.CUSTOM,
        custom_name="wedding_candid",
        base_fps=2.2,
        dense_fps=7.5,
        novelty_threshold=0.032,
        min_sharpness_score=22.0,
        motion_blur_penalty=1.4,
    )
    saved_dict = manager.save_preset("wedding_candid", custom_cfg)
    assert saved_dict["custom_name"] == "wedding_candid"
    assert storage_file.exists()

    # Re-read through a fresh manager instance pointing to the same file
    manager2 = PresetManager(storage_file=storage_file)
    assert "wedding_candid" in manager2.list_all_presets()

    loaded_cfg = manager2.get_preset_config("wedding_candid")
    assert loaded_cfg is not None
    assert loaded_cfg.preset == DomainPreset.CUSTOM
    assert loaded_cfg.custom_name == "wedding_candid"
    assert loaded_cfg.base_fps == 2.2
    assert loaded_cfg.dense_fps == 7.5
    assert loaded_cfg.novelty_threshold == 0.032
    assert loaded_cfg.min_sharpness_score == 22.0
    assert loaded_cfg.motion_blur_penalty == 1.4


def test_preset_manager_delete(tmp_path):
    storage_file = tmp_path / "test_presets.json"
    manager = PresetManager(storage_file=storage_file)

    # Cannot delete built-ins
    assert manager.delete_preset("portrait") is False
    assert manager.delete_preset("custom") is False

    # Save and delete a custom preset
    manager.save_preset("temp_preset", {"base_fps": 2.0})
    assert "temp_preset" in manager.list_all_presets()

    deleted = manager.delete_preset("temp_preset")
    assert deleted is True
    assert "temp_preset" not in manager.list_all_presets()
