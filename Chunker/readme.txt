Currently it gets its data from news_ingestion.

If you want to cahnge that, go to chunk_documents.py and change:

DEFAULT_INPUT = PROJECT_ROOT / "news_ingestion" / "output" / "_test.jsonl"