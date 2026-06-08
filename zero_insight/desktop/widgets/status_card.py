from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

STATUS_COLORS = {
    "OK": "#16A34A",
    "WARNING": "#F59E0B",
    "ERROR": "#DC2626",
    "NONE": "#6B7280",
}


class StatusCard(QFrame):
    def __init__(self, title: str, status: str = "NONE", detail: str = "") -> None:
        super().__init__()
        self.setObjectName("Card")
        self.title_label = QLabel(title)
        self.status_label = QLabel(status)
        self.detail_label = QLabel(detail)
        self.detail_label.setObjectName("Muted")
        self.detail_label.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.detail_label)
        self.set_status(status, detail)

    def set_status(self, status: str, detail: str = "") -> None:
        color = STATUS_COLORS.get(status, STATUS_COLORS["NONE"])
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 700;")
        self.detail_label.setText(detail)
