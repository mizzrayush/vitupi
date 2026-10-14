"""
Vitupi GUI Quick Launcher script.

Usage:
    python run_gui.py
    .venv\\Scripts\\python run_gui.py [video_path]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vitupi.gui import launch_gui

if __name__ == "__main__":
    init_v = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(launch_gui(initial_video=init_v))
