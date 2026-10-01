import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from d_zen.core.logsetup import setup_logging
from d_zen.ui.main_window import MainWindow
from d_zen.ui.theme import STYLESHEET


def _icon_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "assets" / "icon.png"
    return Path(__file__).resolve().parents[2] / "assets" / "icon.png"


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("D-ZEN")
    app.setStyleSheet(STYLESHEET)
    app.setWindowIcon(QIcon(str(_icon_path())))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
