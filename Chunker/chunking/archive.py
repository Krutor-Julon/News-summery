"""
Archivierung der angereicherten Original-Dokumente (ein JSONL pro Run).

Dateiname-Schema: "<ISO-Timestamp mit '-' statt ':'>_<run_id>.jsonl"
Beispiel: 2026-07-16T15-22-53.821Z_8fd3a4.jsonl

Der run_id-Teil (6 Hex-Zeichen, zufällig) verhindert Kollisionen, falls
mehrere Prozesse zeitgleich laufen und zufällig auf dieselbe Millisekunde
treffen.
"""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def generate_run_id() -> str:
    return secrets.token_hex(3)  # 6 Hex-Zeichen


def generate_run_filename(run_id: Optional[str] = None) -> str:
    run_id = run_id or generate_run_id()
    now = datetime.now(timezone.utc)
    # z.B. 2026-07-16T15-22-53.821Z
    ts = now.strftime("%Y-%m-%dT%H-%M-%S.") + f"{now.microsecond // 1000:03d}Z"
    return f"{ts}_{run_id}.jsonl"


class JsonlWriter:
    """Simpler Append-Writer für JSONL-Dateien (ein JSON-Objekt pro Zeile)."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8")

    def write(self, obj: dict[str, Any]) -> None:
        self._fh.write(json.dumps(obj, ensure_ascii=False))
        self._fh.write("\n")

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "JsonlWriter":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
