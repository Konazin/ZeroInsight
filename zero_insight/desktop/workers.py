from __future__ import annotations

import traceback
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class Worker(QObject):
    log = Signal(str, str)
    progress = Signal(int, str)
    result = Signal(object)
    error = Signal(str, str)
    finished = Signal()

    def __init__(self, task: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.task = task
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self) -> None:
        try:
            self.kwargs.setdefault("on_log", self.log.emit)
            self.progress.emit(10, "Iniciando")
            data = self.task(*self.args, **self.kwargs)
            self.progress.emit(100, "Concluido")
            self.result.emit(data)
        except Exception as exc:
            self.error.emit(str(exc), traceback.format_exc())
        finally:
            self.finished.emit()
