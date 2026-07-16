import yaml

from connectors.factory import ConnectorFactory

from utils.deduplication import remove_duplicates
from utils.io import save_jsonl

from extractors.trafilatura_extractor import TrafilaturaExtractor

def load_config(
    path="config/sources.yaml"
):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return yaml.safe_load(f)



def ingest_news():


    config = load_config()


    all_articles = []


    for source in config["sources"]:


        print(
            f"Fetching: {source['name']}"
        )


        connector = ConnectorFactory.create(
            source
        )


        articles = connector.fetch()


        print(
            f"Received {len(articles)} articles"
        )


        all_articles.extend(
            articles
        )



    print(
        f"Total before deduplication: {len(all_articles)}"
    )

    all_articles = remove_duplicates(
        all_articles
    )

    extractor = TrafilaturaExtractor()

    for article in all_articles:

        print(
            f"Extracting: {article.title}"
        )

        extracted_text = extractor.extract(
            article.url
        )

        if extracted_text and len(extracted_text) > 500:

            article.content = extracted_text

            article.content_source = "trafilatura"

        else:

            if article.content:
                article.content_source = "rss"
            else:
                article.content_source = "none"

    save_jsonl(
        all_articles,
        "output/articles.jsonl"
    )


    return all_articles