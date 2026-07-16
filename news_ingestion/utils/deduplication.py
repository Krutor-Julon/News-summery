from models.news_article import NewsArticle


def remove_duplicates(
    articles: list[NewsArticle]
) -> list[NewsArticle]:

    seen_urls = set()

    unique_articles = []


    for article in articles:

        if not article.url:
            continue


        if article.url in seen_urls:
            continue


        seen_urls.add(
            article.url
        )

        unique_articles.append(
            article
        )


    return unique_articles