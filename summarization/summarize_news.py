#from utils.io import load_jsonl, save_jsonl                    # OLD
#from summarizers.ollama_summarizer import OllamaSummarizer     # OLD
# ->
from shared.io import load_jsonl, save_jsonl                   # NEW
from summarization.ollama_summarizer import OllamaSummarizer   # NEW


def summarize_news(
    input_path: str = "output/articles_translated.jsonl",
    output_path: str = "output/articles_summarized.jsonl",
    limit=None,
):
    articles = load_jsonl(input_path)

    if limit:
        articles = articles[:limit]

    print(f"Loaded {len(articles)} articles to summarize.")

    summarizer = OllamaSummarizer()

    for i, article in enumerate(articles, start=1):
        title = article.translated_title or article.title or ""
        text = article.translated_content or ""

        print(f"[{i}/{len(articles)}] Summarizing: {title[:60]}")

        article.summary = summarizer.summarize(title, text)

    save_jsonl(articles, output_path)
    print(f"Done. Saved {len(articles)} summarized articles to {output_path}")
    return articles