from pipeline.ingest_news import ingest_news



if __name__ == "__main__":

    articles = ingest_news()


    print(
        f"Finished. {len(articles)} articles ready."
    )