"""
API-Key kommt nicht aus sources.yaml, sondern aus einer Environment Variable.

Windows:
set NEWSAPI_KEY=dein_key
Linux:
export NEWSAPI_KEY=dein_key
"""
import os
import requests

from dateutil import parser as date_parser

from connectors.base import NewsConnector
#from models.news_article import NewsArticle          # old
from shared.models.news_article import NewsArticle    # new


class NewsAPIConnector(NewsConnector):


    BASE_URL = (
        "https://newsapi.org/v2/everything"
    )


    def fetch(self) -> list[NewsArticle]:

        api_key = os.getenv(
            "NEWSAPI_KEY"
        )

        if not api_key:
            print(
                "[NEWSAPI] Missing API key"
            )
            return []


        params = {

            "apiKey": api_key,

            "q": self.config.get(
                "query",
                "technology"
            ),

            "language": self.config.get(
                "language",
                "en"
            ),

            "pageSize": 100
        }


        articles = []


        try:

            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=10
            )


            response.raise_for_status()


            data = response.json()


            for item in data.get(
                "articles",
                []
            ):

                published = None

                if item.get(
                    "publishedAt"
                ):
                    published = date_parser.parse(
                        item["publishedAt"]
                    )


                article = NewsArticle(

                    title=item.get(
                        "title",
                        ""
                    ),

                    url=item.get(
                        "url",
                        ""
                    ),

                    source=item.get(
                        "source",
                        {}
                    ).get(
                        "name",
                        "NewsAPI"
                    ),

                    published_at=published,

                    description=item.get(
                        "description"
                    ),

                    content=item.get(
                        "content"
                    ),

                    author=item.get(
                        "author"
                    ),

                    image_url=item.get(
                        "urlToImage"
                    ),

                    source_type="api",

                    language=self.config.get(
                        "language"
                    ),

                    raw=item
                )


                articles.append(article)



        except Exception as e:

            print(
                f"[NEWSAPI ERROR] {e}"
            )


        return articles