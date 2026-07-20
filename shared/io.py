import json

from dateutil import parser as date_parser

#from models.news_article import NewsArticle          # OLD
from shared.models.news_article import NewsArticle    # NEW


def save_jsonl(articles: list[NewsArticle], filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        for article in articles:
            json.dump(article.to_dict(), f, ensure_ascii=False)
            f.write("\n")


def load_jsonl(filename: str) -> list[NewsArticle]:
    articles = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if data.get("published_at"):
                try:
                    data["published_at"] = date_parser.parse(data["published_at"])
                except Exception:
                    data["published_at"] = None
            articles.append(NewsArticle(**data))
    return articles