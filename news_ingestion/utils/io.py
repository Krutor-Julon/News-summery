import json

from models.news_article import NewsArticle



def save_jsonl(
    articles: list[NewsArticle],
    filename: str
):

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:


        for article in articles:

            json.dump(
                article.to_dict(),
                f,
                ensure_ascii=False
            )

            f.write("\n")