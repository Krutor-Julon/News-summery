import feedparser

from dateutil import parser as date_parser

from connectors.base import NewsConnector
from models.news_article import NewsArticle


class RSSConnector(NewsConnector):

    def fetch(self) -> list[NewsArticle]:

        url = self.config["url"]
        source_name = self.config["name"]

        articles = []

        try:
            feed = feedparser.parse(url)

            for entry in feed.entries:

                published = None

                if hasattr(entry, "published"):
                    try:
                        published = date_parser.parse(
                            entry.published
                        )
                    except Exception:
                        pass


                article = NewsArticle(
                    title=entry.get(
                        "title",
                        "No title"
                    ),

                    url=entry.get(
                        "link",
                        ""
                    ),

                    source=source_name,

                    content_source="rss",

                    published_at=published,

                    description=entry.get(
                        "summary",
                        None
                    ),

                    content=entry.get(
                        "summary",
                        None
                    ),

                    source_type="rss",

                    language=self.config.get(
                        "language",
                        None
                    ),

                    raw=dict(entry)
                )

                articles.append(article)


        except Exception as e:
            print(
                f"[RSS ERROR] {source_name}: {e}"
            )


        return articles