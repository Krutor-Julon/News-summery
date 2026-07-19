#!/usr/bin/env python3
"""
CLI-Einstiegspunkt: liest eine Input-JSONL mit News-Artikeln, chunkt den
Content jedes Artikels und schreibt Chunks + Archiv gemäß config/chunking.yaml.

Ohne --input wird automatisch die Datei
"<Projekt-Root>/news_ingestion/output/_test.jsonl" verwendet (Output des
Scraper-Teils des Projekts).

Aufruf:
    python chunk_documents.py
    python chunk_documents.py --input pfad/zu/input.jsonl
    python chunk_documents.py --input pfad/zu/input.jsonl --config config/chunking.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chunking.pipeline import run_pipeline

# Dieses Skript liegt in <Projekt-Root>/Chunker/chunk_documents.py.
# Der Scraper-Teil ("news_ingestion") liegt daneben, auf Höhe des Projekt-Root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "news_ingestion" / "output" / "_test.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(description="News-Content in Chunks aufteilen.")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Pfad zur Input-JSONL-Datei (Default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Pfad zur chunking.yaml (Default: config/chunking.yaml relativ zu diesem Skript)",
    )
    args = parser.parse_args()

    news_ingestion_root = Path(__file__).resolve().parent

    if not args.input.exists():
        print(f"Input-Datei nicht gefunden: {args.input}", file=sys.stderr)
        return 1

    summary = run_pipeline(
        input_path=args.input,
        news_ingestion_root=news_ingestion_root,
        config_path=args.config,
    )

    print(
        f"Run {summary['run_id']}: {summary['document_count']} Dokumente, "
        f"{summary['chunk_count']} Chunks."
    )
    print(f"Chunks:  {summary['chunks_file']}")
    print(f"Archiv:  {summary['archive_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
