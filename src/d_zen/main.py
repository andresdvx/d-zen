import sys

from PySide6.QtWidgets import QApplication

from d_zen.ui.main_window import MainWindow
from d_zen.ui.theme import STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("D-ZEN")
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
