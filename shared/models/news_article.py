from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NewsArticle:
    """Einheitliches Format für alle Nachrichtenquellen."""

    title: str
    url: str
    source: str

    published_at: Optional[datetime] = None
    description: Optional[str] = None
    content: Optional[str] = None
    content_source: str = "unknown"
    author: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    source_type: Optional[str] = None

    # --- new fields for the translate / summarize stages ---
    translated_title: Optional[str] = None
    translated_content: Optional[str] = None
    summary: Optional[str] = None

    tags: list[str] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    def to_dict(self):
        """JSON-friendly representation."""
        data = self.__dict__.copy()
        if self.published_at:
            data["published_at"] = self.published_at.isoformat()
        return data