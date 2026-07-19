from pipeline.summarize_news import summarize_news


if __name__ == "__main__":
    # First run: just 3 articles to confirm it works.
    # Then change limit=3 to limit=None for the whole feed.
    summarize_news(limit=None)