"""Executa coroutines a partir de código síncrono (menu, CLI, IDEs com loop ativo)."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable, Coroutine
from typing import TypeVar

T = TypeVar("T")

CoroFactory = Callable[[], Coroutine[object, object, T]]


def run_coro(factory: CoroFactory) -> T:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())

    result: list[T] = []
    error: list[BaseException] = []

    def _worker() -> None:
        try:
            result.append(asyncio.run(factory()))
        except BaseException as exc:
            error.append(exc)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    thread.join()

    if error:
        raise error[0]
    return result[0]
