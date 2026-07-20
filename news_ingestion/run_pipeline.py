import sys
import os

# Make the parent folder importable so `shared`, `translation`,
# and `summarization` can be found when we run from inside news_ingestion.
_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from build_website import build_website
from pipeline.ingest_news import ingest_news
from translation.translate_news import translate_news        # was pipeline.translate_news
from summarization.summarize_news import summarize_news       # was pipeline.summarize_news
from shared.io import load_jsonl, save_jsonl                  # was utils.io


DATABASE = "output/database.jsonl"


def get_known_urls():
    if not os.path.exists(DATABASE):
        return set()
    return {a.url for a in load_jsonl(DATABASE) if a.url}


def run_pipeline():
    known_urls = get_known_urls()
    print(f"Database currently holds {len(known_urls)} articles.")

    # 1. Ingest — fetch the feed, keep only articles we haven't done before
    new_articles = ingest_news(known_urls=known_urls)

    if not new_articles:
        print("No new articles found. Everything is already up to date.")
        return

    print(f"\n{len(new_articles)} new article(s) to process.\n")

    # 2. Translate the new batch
    translate_news()

    # 3. Summarize the new batch
    summarize_news()

    # 4. Add the freshly finished articles into the master database
    newly_done = load_jsonl("output/articles_summarized.jsonl")
    existing = load_jsonl(DATABASE) if os.path.exists(DATABASE) else []
    combined = existing + newly_done
    save_jsonl(combined, DATABASE)

    print(f"\nDone. Database now holds {len(combined)} articles total.")
    build_website()


if __name__ == "__main__":
    run_pipeline()