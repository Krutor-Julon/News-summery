import os
import requests

from dateutil import parser as date_parser

from connectors.base import NewsConnector
from models.news_article import NewsArticle



class GNewsConnector(NewsConnector):


    BASE_URL = (
        "https://gnews.io/api/v4/search"
    )


    def fetch(self):

        api_key = os.getenv(
            "GNEWS_KEY"
        )


        if not api_key:

            print(
                "[GNEWS] Missing API key"
            )

            return []


        params = {

            "apikey": api_key,

            "q": self.config.get(
                "query",
                "technology"
            ),

            "lang": self.config.get(
                "language",
                "en"
            ),

            "max": 100

        }


        articles = []


        try:

            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=10
            )

            response.raise_for_status()


            data=response.json()


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


                articles.append(

                    NewsArticle(

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
                            "GNews"
                        ),

                        published_at=published,

                        description=item.get(
                            "description"
                        ),

                        content=item.get(
                            "content"
                        ),

                        image_url=item.get(
                            "image"
                        ),

                        source_type="api",

                        language=self.config.get(
                            "language"
                        ),

                        raw=item
                    )
                )


        except Exception as e:

            print(
                f"[GNEWS ERROR] {e}"
            )


        return articles