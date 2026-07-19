"""
Zentrale Datenmodelle für die Chunking-Pipeline.

`RawDocument` bildet ein einzelnes Input-JSON-Objekt ab (so wie es aus dem
News-Scraper kommt). `ChunkRecord` ist ein einzelner Chunk-Output-Eintrag,
wie er in die Chunk-JSONL-Datei geschrieben wird.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RawDocument:
    """One line of the JSON"""

    raw: dict[str, Any]

    document_id: Optional[int] = None
    document_uid: Optional[str] = None

    @property
    def title(self) -> str:
        return self.raw.get("title") or ""

    @property
    def content(self) -> str:
        return self.raw.get("content") or ""

    @property
    def source(self) -> str:
        return self.raw.get("source") or ""

    @property
    def published_at(self) -> str:
        return self.raw.get("published_at") or ""

    def as_archive_dict(self) -> dict[str, Any]:
        """Original-JSON + document_id/document_uid für die Archivdatei."""
        enriched = dict(self.raw)
        enriched["document_id"] = self.document_id
        enriched["document_uid"] = self.document_uid
        return enriched


@dataclass
class ChunkRecord:
    """Ein einzelner Chunk, so wie er in die Chunks-JSONL geschrieben wird."""

    document_id: Optional[int]
    document_uid: str
    chunk_id: str
    chunk_index: int
    chunk_count: int
    title: str
    source: str
    published_at: str
    embedding_text: str
    token_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_uid": self.document_uid,
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "chunk_count": self.chunk_count,
            "title": self.title,
            "source": self.source,
            "published_at": self.published_at,
            "embedding_text": self.embedding_text,
            "token_count": self.token_count,
        }


@dataclass
class ChunkingConfig:
    """Getypte Sicht auf die chunking.yaml (Sektion `chunking`)."""

    target_tokens: int = 600
    overlap_percent: float = 0.10
    minimum_chunk_tokens: int = 450
    include_title: bool = True
    preserve_paragraphs: bool = True

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ChunkingConfig":
        return cls(
            target_tokens=int(d.get("target_tokens", 600)),
            overlap_percent=float(d.get("overlap_percent", 0.10)),
            minimum_chunk_tokens=int(d.get("minimum_chunk_tokens", 450)),
            include_title=bool(d.get("include_title", True)),
            preserve_paragraphs=bool(d.get("preserve_paragraphs", True)),
        )
