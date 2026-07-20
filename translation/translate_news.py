#from utils.io import load_jsonl, save_jsonl                 # OLD
#from translators.opus_translator import OpusTranslator      # OLD

from shared.io import load_jsonl, save_jsonl                # NEW
from translation.opus_translator import OpusTranslator      # NEW


def translate_news(
    input_path: str = "output/articles.jsonl",
    output_path: str = "output/articles_translated.jsonl",
    limit=None,
):
    articles = load_jsonl(input_path)

    if limit:
        articles = articles[:limit]

    print(f"Loaded {len(articles)} articles to translate.")

    translator = OpusTranslator()

    for i, article in enumerate(articles, start=1):
        print(f"[{i}/{len(articles)}] Translating: {article.title[:60]}")

        source_text = article.content or article.description or ""

        if article.language == "en":
            article.translated_title = article.title
            article.translated_content = source_text
        else:
            article.translated_title = translator.translate(article.title)
            article.translated_content = translator.translate(source_text)


    # Keep only the translated article + downstream metadata;
    # drop the original-language body so it isn't packed in the same record.
    for article in articles:
        article.content = None
        article.description = None
        article.raw = {}
        #article.title = None           #If you want to blank the german title

    
    save_jsonl(articles, output_path)
    print(f"Done. Saved {len(articles)} translated articles to {output_path}")
    return articles