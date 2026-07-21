#!/usr/bin/env python3
"""
Embedder — the "verknüpfen" step.

It takes three things and wires them together:
  1. the chunks  (JSONL produced by the Chunker)
  2. the embedding model  (multilingual-e5-base)
  3. the vector database  (Milvus Lite, a single local file)

For every chunk it turns the `embedding_text` into a 768-number vector and
stores that vector together with the chunk's metadata in Milvus Lite.

Run it from the PROJECT ROOT, with your virtual environment active:

    python Embedder/embed_and_store.py                 # newest chunk file
    python Embedder/embed_and_store.py --input Chunker/chunks/<run>.jsonl
    python Embedder/embed_and_store.py --recreate      # wipe & rebuild the collection

Re-running is safe: the chunk_id is the primary key, so the same chunk is
updated in place instead of being duplicated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Optional

import yaml
from pymilvus import DataType, MilvusClient
from sentence_transformers import SentenceTransformer

# This file lives in <project_root>/Embedder/. The Chunker sits next to it.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = Path(__file__).resolve().parent / "config" / "embedding.yaml"
CHUNKS_DIR = PROJECT_ROOT / "Chunker" / "chunks"


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_input(cli_input: Optional[Path], cfg: dict[str, Any]) -> Path:
    """Decide which chunks file to read: --input > config > newest in Chunker/chunks."""
    if cli_input:
        return cli_input
    configured = (cfg.get("input", {}) or {}).get("chunks_file") or ""
    if configured:
        p = Path(configured)
        return p if p.is_absolute() else (PROJECT_ROOT / p)
    candidates = sorted(CHUNKS_DIR.glob("*.jsonl"))
    if not candidates:
        raise FileNotFoundError(
            f"No chunk files found in {CHUNKS_DIR}. Run the Chunker first."
        )
    return candidates[-1]  # filenames start with a timestamp, so last == newest


def read_chunks(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("embedding_text"):
                records.append(rec)
    return records


def _clip(value: Any, max_chars: int) -> str:
    """Milvus VARCHAR fields have a max length, so keep strings within bounds."""
    return (str(value) if value is not None else "")[:max_chars]


def build_collection(
    client: MilvusClient,
    name: str,
    dim: int,
    index_type: str,
    metric_type: str,
    recreate: bool,
) -> None:
    if client.has_collection(name):
        if recreate:
            client.drop_collection(name)
        else:
            return  # collection already exists, just add/update rows

    schema = client.create_schema(auto_id=False, enable_dynamic_field=True)
    schema.add_field("chunk_id", DataType.VARCHAR, is_primary=True, max_length=128)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=dim)
    schema.add_field("document_id", DataType.INT64)
    schema.add_field("document_uid", DataType.VARCHAR, max_length=64)
    schema.add_field("chunk_index", DataType.INT64)
    schema.add_field("chunk_count", DataType.INT64)
    schema.add_field("title", DataType.VARCHAR, max_length=1024)
    schema.add_field("source", DataType.VARCHAR, max_length=256)
    schema.add_field("published_at", DataType.VARCHAR, max_length=64)
    schema.add_field("token_count", DataType.INT64)
    schema.add_field("embedding_text", DataType.VARCHAR, max_length=65535)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="vector", index_type=index_type, metric_type=metric_type
    )
    client.create_collection(collection_name=name, schema=schema, index_params=index_params)
    print(f"Created collection '{name}' (dim={dim}, index={index_type}, metric={metric_type}).")


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed chunks and store them in Milvus Lite.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, default=None, help="Path to a chunks .jsonl file")
    parser.add_argument("--recreate", action="store_true", help="Drop and rebuild the collection")
    args = parser.parse_args()

    cfg = load_config(args.config)
    model_cfg = cfg["model"]
    store_cfg = cfg["vector_store"]

    # 1. Read the chunks -------------------------------------------------
    input_path = resolve_input(args.input, cfg)
    print(f"Reading chunks from: {input_path}")
    records = read_chunks(input_path)
    if not records:
        print("No chunks with embedding_text found. Nothing to do.")
        return 0
    print(f"{len(records)} chunks to embed.")

    # 2. Load the embedding model ---------------------------------------
    print(f"Loading embedding model: {model_cfg['name']}")
    print("(The first run downloads ~1 GB. Later runs use the cached copy.)")
    model = SentenceTransformer(model_cfg["name"])

    # 3. Turn each chunk into a vector ----------------------------------
    passages = [model_cfg["passage_prefix"] + r["embedding_text"] for r in records]
    print("Encoding... (slowest part on a CPU — the progress bar shows batches)")
    vectors = model.encode(
        passages,
        batch_size=int(model_cfg.get("batch_size", 16)),
        normalize_embeddings=bool(model_cfg.get("normalize", True)),
        show_progress_bar=True,
    )

    dim = int(model_cfg.get("dimension", vectors.shape[1]))
    if vectors.shape[1] != dim:
        print(f"Note: model produced {vectors.shape[1]}-dim vectors; using that instead of {dim}.")
        dim = vectors.shape[1]

    # 4. Open Milvus Lite (creates the .db file if it does not exist) ----
    db_abs = Path(store_cfg["db_path"])
    if not db_abs.is_absolute():
        db_abs = PROJECT_ROOT / db_abs
    db_abs.parent.mkdir(parents=True, exist_ok=True)

    client = MilvusClient(uri=str(db_abs))
    build_collection(
        client,
        store_cfg["collection"],
        dim,
        store_cfg.get("index_type", "FLAT"),
        store_cfg.get("metric_type", "COSINE"),
        recreate=args.recreate,
    )

    # 5. Store vectors + metadata ---------------------------------------
    rows: list[dict[str, Any]] = []
    for rec, vec in zip(records, vectors):
        rows.append(
            {
                "chunk_id": _clip(rec.get("chunk_id"), 128),
                "vector": vec.tolist(),
                "document_id": int(rec.get("document_id") or 0),
                "document_uid": _clip(rec.get("document_uid"), 64),
                "chunk_index": int(rec.get("chunk_index") or 0),
                "chunk_count": int(rec.get("chunk_count") or 0),
                "title": _clip(rec.get("title"), 1000),
                "source": _clip(rec.get("source"), 250),
                "published_at": _clip(rec.get("published_at"), 64),
                "token_count": int(rec.get("token_count") or 0),
                "embedding_text": _clip(rec.get("embedding_text"), 60000),
            }
        )

    print(f"Upserting {len(rows)} rows into '{store_cfg['collection']}'...")
    client.upsert(collection_name=store_cfg["collection"], data=rows)

    stats = client.get_collection_stats(store_cfg["collection"])
    print(f"Done. Collection now holds ~{stats.get('row_count', '?')} rows.")
    print(f"Database file: {db_abs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
