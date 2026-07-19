from abc import ABC, abstractmethod
#from models.news_article import NewsArticle          # old
from shared.models.news_article import NewsArticle    # new


class NewsConnector(ABC):

    def __init__(self, config: dict):
        self.config = config


    @abstractmethod
    def fetch(self) -> list[NewsArticle]:
        """
        Muss von jedem Connector implementiert werden.
        """

        pass