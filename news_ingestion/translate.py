from pipeline.translate_news import translate_news


if __name__ == "__main__":
    # First run: translate only the first 5 articles as a quick test.
    # Once it looks good, change limit=5 to limit=None for the full feed.
    translate_news(limit=None)