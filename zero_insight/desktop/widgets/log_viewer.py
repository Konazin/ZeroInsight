from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QPlainTextEdit, QVBoxLayout, QWidget


class LogViewer(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.clear_button = QPushButton("Limpar")
        self.copy_button = QPushButton("Copiar")
        self.clear_button.clicked.connect(self.text.clear)
        self.copy_button.clicked.connect(self.text.selectAll)
        self.copy_button.clicked.connect(self.text.copy)

        actions = QHBoxLayout()
        actions.addWidget(self.copy_button)
        actions.addWidget(self.clear_button)
        actions.addStretch(1)
        layout = QVBoxLayout(self)
        layout.addLayout(actions)
        layout.addWidget(self.text)

    def append(self, level: str, message: str) -> None:
        self.text.appendPlainText(f"[{level}] {message}")
