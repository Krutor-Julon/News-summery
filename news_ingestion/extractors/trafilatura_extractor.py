import trafilatura

from extractors.base import ArticleExtractor


class TrafilaturaExtractor(ArticleExtractor):

    def extract(self, url: str) -> str:

        try:

            downloaded = trafilatura.fetch_url(url)

            if not downloaded:
                return ""

            text = trafilatura.extract(
                downloaded,
                include_comments=False
            )

            return text or ""

        except Exception as e:

            print(
                f"[EXTRACT ERROR] {url}: {e}"
            )

            return ""