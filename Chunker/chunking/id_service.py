"""
ID-Vergabe für Dokumente.

- `document_uid`: ein lokal generiertes UUID4 - dafür braucht es keine
  Datenbank, es muss nur global eindeutig sein.
- `document_id`: eine fortlaufende, numerische ID. Gedacht als Milvus-
  Primärschlüssel. Da die Milvus-Instanz noch nicht eingerichtet ist,
  ist diese Klasse so gebaut, dass später einfach ein echter Milvus-
  Client übergeben werden kann (siehe `milvus_client`-Parameter und
  `_fetch_next_id_from_milvus`), ohne den Rest der Pipeline anzufassen.

  Ohne Milvus-Client: es wird einmalig eine Meldung ausgegeben und ab 1
  hochgezählt. Damit IDs auch über mehrere Runs hinweg (ohne DB) nicht
  kollidieren, wird der Zähler zusätzlich in einer kleinen Zähler-Datei
  im config-Ordner persistiert. Das ist ein reiner Übergangs-Mechanismus
  bis Milvus angebunden ist.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Optional


class IdService:
    def __init__(
        self,
        milvus_client: Optional[Any] = None,
        counter_file: Optional[Path] = None,
    ) -> None:
        self._milvus_client = milvus_client
        self._counter_file = counter_file
        self._warned = False
        self._local_counter: Optional[int] = None

        if self._milvus_client is None:
            self._local_counter = self._load_local_counter()

    # -- öffentliche API -----------------------------------------------

    def next_ids(self) -> tuple[int, str]:
        """Liefert (document_id, document_uid) für ein neues Dokument."""
        document_uid = str(uuid.uuid4())
        document_id = self._next_document_id()
        return document_id, document_uid

    # -- intern -----------------------------------------------------------

    def _next_document_id(self) -> int:
        if self._milvus_client is not None:
            return self._fetch_next_id_from_milvus()

        if not self._warned:
            print(
                "[id_service] Keine Milvus-Verbindung konfiguriert - "
                "document_id wird lokal vergeben (Start bei 1)."
            )
            self._warned = True

        assert self._local_counter is not None
        current = self._local_counter
        self._local_counter += 1
        self._save_local_counter(self._local_counter)
        return current

    def _fetch_next_id_from_milvus(self) -> int:  # pragma: no cover
        """
        Platzhalter für die spätere Milvus-Anbindung. Sobald Milvus steht,
        hier z.B. eine Sequenz/Counter-Collection abfragen oder auf
        Auto-ID der Collection zurückgreifen.
        """
        raise NotImplementedError(
            "Milvus-Client ist gesetzt, aber _fetch_next_id_from_milvus "
            "ist noch nicht implementiert."
        )

    def _load_local_counter(self) -> int:
        if self._counter_file and self._counter_file.exists():
            try:
                data = json.loads(self._counter_file.read_text(encoding="utf-8"))
                return int(data.get("next_document_id", 1))
            except (json.JSONDecodeError, ValueError):
                pass
        return 1

    def _save_local_counter(self, next_value: int) -> None:
        if not self._counter_file:
            return
        self._counter_file.parent.mkdir(parents=True, exist_ok=True)
        self._counter_file.write_text(
            json.dumps({"next_document_id": next_value}), encoding="utf-8"
        )
