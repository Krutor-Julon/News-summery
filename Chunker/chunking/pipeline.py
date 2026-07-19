"""
Orchestriert einen Chunking-Run:

1. Input-JSONL einlesen (eine Zeile = ein Artikel-JSON).
2. Pro Dokument: document_id/document_uid vergeben (id_service).
3. Nur das "content"-Feld chunken (chunker) - alles andere ist Metadaten
   für die Vektor-DB und wird 1:1 ins Archiv übernommen.
4. Chunks als JSONL schreiben (chunks/<run>.jsonl).
5. Angereichertes Original als JSONL ins Archiv schreiben (archive/<run>.jsonl),
   sofern archive.enabled in der Config gesetzt ist.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml

from .archive import JsonlWriter, generate_run_filename, generate_run_id
from .chunker import build_chunks
from .id_service import IdService
from .models import ChunkingConfig, ChunkRecord, RawDocument


def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_input_documents(input_path: Path) -> Iterable[RawDocument]:
    """Liest eine JSONL-Datei ein (ein JSON-Objekt pro Zeile)."""
    with input_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Ungültiges JSON in Zeile {line_no} von {input_path}: {exc}") from exc
            yield RawDocument(raw=raw)


def run_pipeline(
    input_path: Path,
    news_ingestion_root: Path,
    config_path: Optional[Path] = None,
    milvus_client: Optional[Any] = None,
) -> dict[str, Any]:
    """
    Führt einen kompletten Chunking-Run aus.

    Gibt eine kleine Zusammenfassung zurück (Pfade + Anzahl Dokumente/Chunks),
    nützlich fürs Testen und für Logging im CLI-Skript.
    """
    config_path = config_path or (news_ingestion_root / "config" / "chunking.yaml")
    raw_config = load_config(config_path)
    chunk_cfg = ChunkingConfig.from_dict(raw_config.get("chunking", {}))
    archive_enabled = bool(raw_config.get("archive", {}).get("enabled", True))
    write_chunk_jsonl = bool(raw_config.get("output", {}).get("write_chunk_jsonl", True))

    run_id = generate_run_id()
    run_filename = generate_run_filename(run_id)

    chunks_dir = news_ingestion_root / "chunks"
    archive_dir = news_ingestion_root / "archive"

    id_service = IdService(
        milvus_client=milvus_client,
        counter_file=news_ingestion_root / "config" / ".id_counter.json",
    )

    chunk_writer: Optional[JsonlWriter] = None
    if write_chunk_jsonl:
        chunk_writer = JsonlWriter(chunks_dir / run_filename)

    archive_writer: Optional[JsonlWriter] = None
    if archive_enabled:
        archive_writer = JsonlWriter(archive_dir / run_filename)

    doc_count = 0
    chunk_count_total = 0

    try:
        for doc in read_input_documents(input_path):
            document_id, document_uid = id_service.next_ids()
            doc.document_id = document_id
            doc.document_uid = document_uid
            doc_count += 1

            if archive_writer is not None:
                archive_writer.write(doc.as_archive_dict())

            if chunk_writer is not None:
                built = build_chunks(
                    title=doc.title,
                    content=doc.content,
                    target_tokens=chunk_cfg.target_tokens,
                    overlap_percent=chunk_cfg.overlap_percent,
                    minimum_chunk_tokens=chunk_cfg.minimum_chunk_tokens,
                    include_title=chunk_cfg.include_title,
                    preserve_paragraphs=chunk_cfg.preserve_paragraphs,
                )
                chunk_total = len(built)
                for idx, chunk in enumerate(built):
                    record = ChunkRecord(
                        document_id=document_id,
                        document_uid=document_uid,
                        chunk_id=f"{document_uid}_{idx:04d}",
                        chunk_index=idx,
                        chunk_count=chunk_total,
                        title=doc.title,
                        source=doc.source,
                        published_at=doc.published_at,
                        embedding_text=chunk.embedding_text,
                        token_count=chunk.token_count,
                    )
                    chunk_writer.write(record.to_dict())
                    chunk_count_total += 1
    finally:
        if chunk_writer is not None:
            chunk_writer.close()
        if archive_writer is not None:
            archive_writer.close()

    return {
        "run_id": run_id,
        "run_filename": run_filename,
        "document_count": doc_count,
        "chunk_count": chunk_count_total,
        "chunks_file": str(chunks_dir / run_filename) if write_chunk_jsonl else None,
        "archive_file": str(archive_dir / run_filename) if archive_enabled else None,
    }
