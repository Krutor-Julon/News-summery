from abc import ABC, abstractmethod


class ArticleExtractor(ABC):

    @abstractmethod
    def extract(self, url: str) -> str:
        pass