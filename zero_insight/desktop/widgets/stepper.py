from __future__ import annotations

from PySide6.QtWidgets import QLabel


class Stepper(QLabel):
    def set_step(self, text: str) -> None:
        self.setText(text)
