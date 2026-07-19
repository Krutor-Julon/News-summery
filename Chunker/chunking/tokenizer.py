"""
Tokenzählung sowie Satz- und Absatz-Splitting.

Tokenzählung nutzt tiktoken (cl100k_base), falls verfügbar. Das ist
modellunabhängig gut genug für eine Token-Budgetierung beim Chunking; für
exakte Embedding-Modell-Tokens müsste man den passenden Tokenizer des
jeweiligen Embedding-Modells einsetzen. Fällt tiktoken aus irgendeinem
Grund weg (z.B. nicht installiert), wird auf eine grobe Wortschätzung
zurückgefallen (~0.75 Tokens/Wort im Deutschen eher konservativ, daher
hier 1 Token pro Wort als Approximation).
"""
from __future__ import annotations

import re
from typing import Sequence

try:
    import tiktoken

    _ENCODER = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - Fallback falls tiktoken fehlt
    _ENCODER = None


def count_tokens(text: str) -> int:
    """Zählt Tokens in `text`. Leerer String -> 0."""
    if not text:
        return 0
    if _ENCODER is not None:
        return len(_ENCODER.encode(text))
    # Fallback: grobe Wortschätzung
    return len(text.split())


# Sentence-Split: trennt an Satzzeichen (. ! ?), gefolgt von Whitespace und
# einem Großbuchstaben (inkl. Umlaute) oder Zeilenende. Bewusst simpel
# gehalten (kein NLP-Modell) - reicht für "Sätze nicht abschneiden".
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ0-9\"'])")


def split_sentences(text: str) -> list[str]:
    """Zerlegt einen Textblock in Sätze, ohne Sätze anzuschneiden."""
    text = text.strip()
    if not text:
        return []
    parts = _SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def split_paragraphs(text: str) -> list[str]:
    """Zerlegt Text an Zeilenumbrüchen in Absätze (leere Zeilen entfernt)."""
    return [p.strip() for p in text.split("\n") if p.strip()]


def split_into_units(text: str, preserve_paragraphs: bool = True) -> list[str]:
    """
    Liefert die "Grundeinheiten" für den Chunk-Aufbau.

    Wenn preserve_paragraphs=True und der Text tatsächlich mehr als einen
    Absatz enthält (\\n als Trenner), werden Absätze als Einheiten genutzt.
    Andernfalls (kein \\n vorhanden, oder preserve_paragraphs=False) wird
    auf Satzebene zurückgefallen - das deckt den Fall ab, dass \\n nicht
    zuverlässig Abschnitte markiert.
    """
    if preserve_paragraphs:
        paragraphs = split_paragraphs(text)
        if len(paragraphs) > 1:
            return paragraphs
    return split_sentences(text)


def split_unit_if_too_large(unit: str, target_tokens: int) -> list[str]:
    """
    Falls eine einzelne Einheit (typischerweise ein Absatz) für sich allein
    schon größer als target_tokens ist, wird sie auf Satzebene weiter
    zerlegt, damit ein einzelner Chunk nicht beliebig groß werden kann.
    Ein einzelner Satz, der selbst > target_tokens ist, bleibt unangetastet
    (Sätze werden nie angeschnitten).
    """
    if count_tokens(unit) <= target_tokens:
        return [unit]
    sentences = split_sentences(unit)
    return sentences if sentences else [unit]
