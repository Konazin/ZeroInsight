from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from zero_insight.desktop.main_window import MainWindow
from zero_insight.desktop.theme import APP_STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ZeroInsight")
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
