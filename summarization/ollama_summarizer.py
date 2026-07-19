import requests


class OllamaSummarizer:
    """Summarizes English text using a local Ollama model."""

    def __init__(
        self,
        model: str = "llama3.2:3b",
        host: str = "http://localhost:11434",
        num_ctx: int = 8192,
    ):
        self.model = model
        self.url = f"{host}/api/generate"
        self.num_ctx = num_ctx

    def summarize(self, title: str, text: str) -> str:
        if not text or not text.strip():
            return ""

        prompt = (
            "Summarize the following news article in 2-3 clear sentences. "
            "Write only the summary, with no preamble.\n\n"
            f"Title: {title}\n\n"
            f"Article:\n{text}"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": self.num_ctx,
                "temperature": 0.3,
            },
        }

        try:
            response = requests.post(self.url, json=payload, timeout=300)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"[SUMMARIZE ERROR] {e}")
            return ""