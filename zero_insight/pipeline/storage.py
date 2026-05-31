from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    line = json.dumps(
        {"timestamp": datetime.now(timezone.utc).isoformat(), **data},
        ensure_ascii=False,
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
