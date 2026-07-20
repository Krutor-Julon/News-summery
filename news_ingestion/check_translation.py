import json
import random

path = "output/articles_translated.jsonl"

with open(path, "r", encoding="utf-8") as f:
    articles = [json.loads(line) for line in f if line.strip()]

sample = random.sample(articles, min(3, len(articles)))

for i, a in enumerate(sample, start=1):
    print("=" * 70)
    print(f"ARTICLE {i}")
    print("=" * 70)
    print("DE title:", a.get("title", ""))
    print("EN title:", a.get("translated_title", ""))
    print()
    print("DE content:", (a.get("content") or "")[:400])
    print()
    print("EN content:", (a.get("translated_content") or "")[:400])
    print()