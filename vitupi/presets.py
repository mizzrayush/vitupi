"""
Preset management and persistent storage for Vitupi extraction profiles.
Enables creating, loading, customizing, and persisting custom presets to disk.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from vitupi.config import DomainPreset, ExtractionMode, VitupiConfig, get_preset_defaults

PRESETS_DIR_NAME = ".vitupi"
PRESETS_FILENAME = "presets.json"


def get_default_presets_dir() -> Path:
    """Return the user config directory for Vitupi (~/.vitupi)."""
    p = Path.home() / PRESETS_DIR_NAME
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Fallback to local working directory if home is not writable
        p = Path(".")
    return p


def get_default_presets_file() -> Path:
    """Return the path to presets.json."""
    return get_default_presets_dir() / PRESETS_FILENAME


class PresetManager:
    """
    Manages persistent custom extraction presets stored on disk as JSON.
    """

    BUILTIN_PRESETS: List[str] = [
        "portrait",
        "candid",
        "sports",
        "security",
        "default",
        "custom",
    ]

    def __init__(self, storage_file: Optional[Union[str, Path]] = None):
        self.storage_file = Path(storage_file) if storage_file else get_default_presets_file()

    def is_builtin(self, name: str) -> bool:
        """Check if a preset name is a system built-in."""
        return name.strip().lower() in self.BUILTIN_PRESETS

    def load_custom_presets(self) -> Dict[str, dict]:
        """Load all custom presets saved on disk."""
        if not self.storage_file.exists():
            return {}
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                return {}
        except Exception:
            return {}

    def save_preset(self, name: str, config: Union[VitupiConfig, dict]) -> dict:
        """
        Save or overwrite a named custom preset to disk.
        
        Args:
            name: Identifier for the preset (e.g. 'drone_aerial' or 'my_candid').
            config: A VitupiConfig instance or dictionary of configuration parameters.
            
        Returns:
            The serialized configuration dictionary stored.
        """
        name_clean = name.strip()
        if not name_clean:
            name_clean = "custom"

        presets = self.load_custom_presets()

        if isinstance(config, VitupiConfig):
            cfg_dict = config.to_dict()
        else:
            cfg_dict = dict(config)

        cfg_dict["custom_name"] = name_clean
        cfg_dict["preset"] = "custom"
        presets[name_clean] = cfg_dict

        # Ensure parent directory exists before writing
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2)

        return cfg_dict

    def delete_preset(self, name: str) -> bool:
        """
        Delete a custom preset from disk. Built-in presets cannot be deleted.
        
        Returns:
            True if preset was found and deleted, False otherwise.
        """
        name_clean = name.strip()
        if self.is_builtin(name_clean):
            return False

        presets = self.load_custom_presets()
        if name_clean in presets:
            del presets[name_clean]
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(presets, f, indent=2)
            return True
        return False

    def list_all_presets(self) -> List[str]:
        """
        Return ordered list of all available presets (built-ins followed by saved custom presets).
        """
        custom_names = sorted(
            [k for k in self.load_custom_presets().keys() if k.lower() not in self.BUILTIN_PRESETS]
        )
        return list(self.BUILTIN_PRESETS) + custom_names

    def get_preset_config(self, name: str) -> VitupiConfig:
        """
        Retrieve a preset as a fully configured VitupiConfig object.
        Checks custom presets first, then falls back to built-ins.
        """
        name_clean = name.strip()
        customs = self.load_custom_presets()

        # Check saved custom preset
        if name_clean in customs:
            return VitupiConfig.from_dict(customs[name_clean])

        # Also check case-insensitive custom names
        for k, v in customs.items():
            if k.lower() == name_clean.lower():
                return VitupiConfig.from_dict(v)

        # Check built-in preset
        try:
            domain_enum = DomainPreset(name_clean.lower())
            return get_preset_defaults(preset=domain_enum)
        except ValueError:
            return get_preset_defaults(preset=DomainPreset.CUSTOM)


# Global default preset manager
_default_manager: Optional[PresetManager] = None


def get_preset_manager() -> PresetManager:
    """Return the global default PresetManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = PresetManager()
    return _default_manager
