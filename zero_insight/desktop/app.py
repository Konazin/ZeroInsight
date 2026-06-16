from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from zero_insight.desktop.main_window import MainWindow
from zero_insight.desktop.theme import APP_STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ZeroInsight")
    base_font = QFont("Segoe UI")
    base_font.setPointSize(10)
    app.setFont(base_font)
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
