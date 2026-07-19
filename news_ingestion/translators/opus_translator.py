import re

from transformers import MarianMTModel, MarianTokenizer


class OpusTranslator:
    """German -> English translation using Helsinki-NLP Opus-MT (runs on CPU)."""

    def __init__(self, model_name: str = "Helsinki-NLP/opus-mt-de-en"):
        print(f"Loading translation model: {model_name} ...")
        self.tokenizer = MarianTokenizer.from_pretrained(model_name)
        self.model = MarianMTModel.from_pretrained(model_name)
        print("Translation model ready.")

    def _split_sentences(self, text: str) -> list[str]:
        # Opus-MT handles ~512 tokens at a time, so split long text into sentences.
        return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]

    def translate(self, text: str) -> str:
        if not text:
            return ""
        translated = []
        sentences = self._split_sentences(text)
        for i in range(0, len(sentences), 8):  # small batches keep memory low
            batch = sentences[i:i + 8]
            encoded = self.tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )
            generated = self.model.generate(**encoded, max_length=512)
            translated.extend(
                self.tokenizer.batch_decode(generated, skip_special_tokens=True)
            )
        return " ".join(translated)