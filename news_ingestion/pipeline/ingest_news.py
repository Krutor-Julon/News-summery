import yaml

from connectors.factory import ConnectorFactory

from utils.deduplication import remove_duplicates
#from utils.io import load_jsonl, save_jsonl          # old
from shared.io import load_jsonl, save_jsonl          # new

from extractors.trafilatura_extractor import TrafilaturaExtractor


def load_config(path="config/sources.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ingest_news(known_urls=None):
    if known_urls is None:
        known_urls = set()

    config = load_config()
    all_articles = []

    for source in config["sources"]:
        print(f"Fetching: {source['name']}")
        connector = ConnectorFactory.create(source)
        articles = connector.fetch()
        print(f"Received {len(articles)} articles")
        all_articles.extend(articles)

    print(f"Total before deduplication: {len(all_articles)}")
    all_articles = remove_duplicates(all_articles)

    # Skip articles we've already processed in a previous run
    before = len(all_articles)
    all_articles = [a for a in all_articles if a.url not in known_urls]
    skipped = before - len(all_articles)
    if skipped:
        print(f"Skipping {skipped} already-processed articles.")
    print(f"New articles to extract: {len(all_articles)}")

    extractor = TrafilaturaExtractor()
    for article in all_articles:
        print(f"Extracting: {article.title}")
        extracted_text = extractor.extract(article.url)
        if extracted_text and len(extracted_text) > 500:
            article.content = extracted_text
            article.content_source = "trafilatura"
        else:
            if article.content:
                article.content_source = "rss"
            else:
                article.content_source = "none"

    save_jsonl(all_articles, "output/articles.jsonl")
    return all_articles