# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for Vitupi Studio.
Builds a standalone, zero-dependency Windows desktop executable.
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all vitupi submodules and data
hidden_imports = [
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.QtSvg",
    "cv2",
    "numpy",
    "PIL",
    "PIL.Image",
    "scenedetect",
    "scenedetect.detectors",
    "scenedetect.detectors.content_detector",
    "scenedetect.detectors.adaptive_detector",
    "scenedetect.scene_manager",
    "platformdirs",
] + collect_submodules("vitupi")

datas = [
    ("assets", "assets"),
]

a = Analysis(
    ["run_gui.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "notebook", "IPython"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Standalone Single-File Executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="VitupiStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed GUI application (no CMD prompt window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico",
)
