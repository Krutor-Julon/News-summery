#!/usr/bin/env python3
"""
A tiny semantic-search demo so you can SEE that the vector database works.

It embeds your question with the same model, asks Milvus Lite for the closest
chunks, and prints them. This is a miniature version of the "retrieval" step
your RAG fact-checker will eventually use.

Run from the project root (venv active):

    python Embedder/search_demo.py "Erdbeben in Venezuela"
    python Embedder/search_demo.py "space law for young astronauts"
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG = Path(__file__).resolve().parent / "config" / "embedding.yaml"


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python Embedder/search_demo.py "your question"')
        return 1
    query = " ".join(sys.argv[1:])

    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    model_cfg, store_cfg = cfg["model"], cfg["vector_store"]

    db_abs = Path(store_cfg["db_path"])
    if not db_abs.is_absolute():
        db_abs = PROJECT_ROOT / db_abs

    model = SentenceTransformer(model_cfg["name"])
    query_vec = model.encode(
        [model_cfg["query_prefix"] + query],
        normalize_embeddings=bool(model_cfg.get("normalize", True)),
    )[0].tolist()

    client = MilvusClient(uri=str(db_abs))
    client.load_collection(store_cfg["collection"])
    results = client.search(
        collection_name=store_cfg["collection"],
        data=[query_vec],
        limit=5,
        search_params={"metric_type": store_cfg.get("metric_type", "COSINE")},
        output_fields=["title", "source", "published_at", "embedding_text"],
    )[0]

    print(f"\nTop matches for: {query!r}\n")
    for i, hit in enumerate(results, 1):
        entity = hit["entity"]
        score = hit["distance"]  # with COSINE, higher = more similar
        snippet = entity.get("embedding_text", "").replace("\n", " ")
        print(f"{i}. [score {score:.3f}] {entity.get('title', '')}  ({entity.get('source', '')})")
        print(f"   {snippet[:200]}...\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
