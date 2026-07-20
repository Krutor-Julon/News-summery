import json

SRC = "news_ingestion/output/database.jsonl"
OUT = "news_ingestion/output/for_chunking.jsonl"

count = 0
with open(SRC, encoding="utf-8") as f_in, open(OUT, "w", encoding="utf-8") as f_out:
    for line in f_in:
        line = line.strip()
        if not line:
            continue
        art = json.loads(line)
        english = (art.get("translated_content") or "").strip()
        if not english:
            continue  # skip anything that wasn't translated
        record = {
            "title": art.get("translated_title") or art.get("title") or "",
            "content": english,          # the chunker chunks THIS field
            "source": art.get("source") or "",
            "published_at": art.get("published_at") or "",
            "url": art.get("url") or "",
        }
        f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
        count += 1

print(f"Wrote {count} English articles to {OUT}")