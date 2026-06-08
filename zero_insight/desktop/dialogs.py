from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def show_actionable_error(parent: QWidget, title: str, message: str, details: str = "") -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(title)
    box.setText(message)
    if details:
        box.setDetailedText(details)
    box.exec()
