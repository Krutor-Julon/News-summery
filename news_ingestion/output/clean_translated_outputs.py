r"""
clean_translated_outputs.py

One-off migration: bring old JSON output records up to the new standard.

Older runs packed the original article (content / description / raw) into the
SAME record as the translated fields. The new translation stage stores only the
translated text plus metadata. This script retro-fixes records produced before
that change by nulling out `content` and `description` and emptying `raw`.

It is idempotent: records that are already clean are left unchanged, so running
it more than once is safe.

Run it from inside the `output` folder:

    cd news_ingestion\output
    python clean_translated_outputs.py

A .bak copy of every file it changes is written next to the original before
anything is overwritten.
"""

import json
import os
import shutil

# Files to clean. NOTE: articles.jsonl is deliberately NOT here — it holds the
# ORIGINAL German article and is supposed to keep content/description.
TARGET_FILES = [
    "articles_translated.jsonl",
    "articles_summarized.jsonl",
    "database.jsonl",
]


def needs_cleaning(record: dict) -> bool:
    """True if the record still carries the original body in some form."""
    return bool(record.get("content")) or bool(record.get("description")) or bool(record.get("raw"))


def clean_record(record: dict) -> dict:
    """Match the new translation-stage standard: drop the original body."""
    record["content"] = None
    record["description"] = None
    record["raw"] = {}
    return record


def clean_file(path: str) -> None:
    if not os.path.exists(path):
        print(f"  skip   {path}  (not found)")
        return

    total = 0
    changed = 0
    cleaned_lines = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            record = json.loads(line)
            if needs_cleaning(record):
                record = clean_record(record)
                changed += 1
            # ensure_ascii=False keeps German umlauts readable, matching save_jsonl
            cleaned_lines.append(json.dumps(record, ensure_ascii=False))

    if changed == 0:
        print(f"  ok     {path}  ({total} records, already clean)")
        return

    # Back up the original before overwriting.
    backup = path + ".bak"
    shutil.copy2(path, backup)

    with open(path, "w", encoding="utf-8") as f:
        for line in cleaned_lines:
            f.write(line + "\n")

    print(f"  fixed  {path}  ({changed} of {total} records cleaned, backup -> {backup})")


def main() -> None:
    print("Cleaning JSON outputs to the new standard...\n")
    for name in TARGET_FILES:
        clean_file(name)
    print("\nDone.")


if __name__ == "__main__":
    main()