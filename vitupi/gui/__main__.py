"""
Vitupi GUI module runner (python -m vitupi.gui).
"""

import sys
from vitupi.gui.app import launch_gui

if __name__ == "__main__":
    init_v = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(launch_gui(initial_video=init_v))
