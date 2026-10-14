"""
Application launcher entry point for Vitupi GUI.
"""

import sys
from PyQt6.QtWidgets import QApplication

from vitupi.gui.main_window import VitupiMainWindow


def launch_gui(initial_video: str = None, fullscreen: bool = True) -> int:
    """Launch the Vitupi PyQt6 GUI application in full screen mode."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName("Vitupi")
    app.setOrganizationName("Vitupi")

    window = VitupiMainWindow(initial_video=initial_video)
    if fullscreen:
        window.showFullScreen()
        window.ribbon.update_fullscreen_state(True)
    else:
        window.showMaximized()
        window.ribbon.update_fullscreen_state(False)
    return app.exec()


if __name__ == "__main__":
    init_v = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(launch_gui(initial_video=init_v))
