"""
Kernlogik des Chunkings.

Ablauf pro Dokument:
1. Content in Grundeinheiten zerlegen (Absätze, falls vorhanden und
   preserve_paragraphs=True; sonst Sätze - Fallback für Content ohne
   verlässliche \\n-Trennung).
2. Überlange Einheiten (einzelner Absatz > target_tokens) werden zusätzlich
   auf Satzebene zerlegt, damit ein Chunk nicht beliebig groß wird.
3. Gierige Paketierung der Einheiten bis target_tokens erreicht ist - dabei
   wird nie ein Satz angeschnitten (target_tokens ist ein weicher Richtwert,
   kein hartes Limit).
4. Ein zu kleiner letzter Chunk (< minimum_chunk_tokens) wird mit dem
   vorherigen Chunk zusammengeführt, statt als Mini-Rest zu verbleiben.
5. Overlap: An den Anfang jedes Chunks (außer dem ersten) wird der
   Tail des vorherigen Chunks angehängt (ca. overlap_percent * target_tokens
   Tokens, satzweise, nicht angeschnitten).
"""
from __future__ import annotations

from dataclasses import dataclass

from .tokenizer import count_tokens, split_paragraphs, split_sentences, split_unit_if_too_large


@dataclass
class BuiltChunk:
    embedding_text: str
    token_count: int


def _split_into_units(content: str, preserve_paragraphs: bool) -> tuple[list[str], str]:
    """Liefert (units, mode) mit mode in {"paragraph", "sentence"}."""
    if preserve_paragraphs:
        paragraphs = split_paragraphs(content)
        if len(paragraphs) > 1:
            return paragraphs, "paragraph"
    return split_sentences(content), "sentence"


def _expand_oversized(units: list[str], target_tokens: int) -> list[str]:
    expanded: list[str] = []
    for unit in units:
        expanded.extend(split_unit_if_too_large(unit, target_tokens))
    return expanded


def _pack_units(units: list[str], target_tokens: int) -> list[list[str]]:
    chunks: list[list[str]] = []
    current: list[str] = []
    current_tokens = 0
    for unit in units:
        unit_tokens = count_tokens(unit)
        if current and current_tokens + unit_tokens > target_tokens:
            chunks.append(current)
            current = [unit]
            current_tokens = unit_tokens
        else:
            current.append(unit)
            current_tokens += unit_tokens
    if current:
        chunks.append(current)
    return chunks


def _merge_small_tail(chunks: list[list[str]], minimum_chunk_tokens: int) -> list[list[str]]:
    """
    Behandelt einen zu kleinen letzten Chunk (< minimum_chunk_tokens).

    Statt den kompletten letzten Chunk an den vorherigen anzuhängen (was
    diesen weit über target_tokens aufblähen kann), werden zunächst nur
    einzelne Einheiten vom Ende des vorherigen Chunks in den kleinen
    Chunk verschoben ("rebalancing"), bis dieser die Mindestgröße
    erreicht. Nur falls der vorherige Chunk dafür nicht genug hergibt
    (z.B. Dokument insgesamt sehr kurz), werden die beiden Chunks
    komplett zusammengeführt.
    """
    while len(chunks) > 1:
        last = chunks[-1]
        last_tokens = sum(count_tokens(u) for u in last)
        if last_tokens >= minimum_chunk_tokens:
            break

        prev = chunks[-2]
        prev_tokens = sum(count_tokens(u) for u in prev)

        # Ermitteln, welche Einheiten vom Ende von prev verschoben werden
        # könnten, OHNE prev selbst unter minimum_chunk_tokens zu drücken.
        movable: list[str] = []
        remaining_prev_tokens = prev_tokens
        gained = 0
        idx = len(prev) - 1
        while idx >= 0 and len(prev) - len(movable) > 1:
            unit_tokens = count_tokens(prev[idx])
            if remaining_prev_tokens - unit_tokens < minimum_chunk_tokens:
                break
            movable.insert(0, prev[idx])
            remaining_prev_tokens -= unit_tokens
            gained += unit_tokens
            idx -= 1
            if last_tokens + gained >= minimum_chunk_tokens:
                break

        if last_tokens + gained >= minimum_chunk_tokens:
            # Rebalancing reicht aus: Einheiten von prev nach last verschieben.
            for _ in movable:
                prev.pop()
            last[:0] = movable
        else:
            # Rebalancing würde prev selbst unter die Mindestgröße drücken
            # und last trotzdem nicht ausreichend füllen -> als letzten
            # Ausweg komplett zusammenführen (Satzintegrität geht vor
            # exakter Zielgröße).
            merged = chunks.pop()
            chunks[-1] = chunks[-1] + merged
    return chunks


def _overlap_prefix(prev_units: list[str], overlap_tokens: int) -> list[str]:
    """Wählt die letzten Einheiten von prev_units, bis ~overlap_tokens erreicht sind."""
    if overlap_tokens <= 0:
        return []
    selected: list[str] = []
    total = 0
    for unit in reversed(prev_units):
        unit_tokens = count_tokens(unit)
        if selected and total + unit_tokens > overlap_tokens:
            break
        selected.insert(0, unit)
        total += unit_tokens
        if total >= overlap_tokens:
            break
    return selected


def _join(units: list[str], mode: str) -> str:
    separator = "\n\n" if mode == "paragraph" else " "
    return separator.join(units)


def build_chunks(
    title: str,
    content: str,
    target_tokens: int,
    overlap_percent: float,
    minimum_chunk_tokens: int,
    include_title: bool,
    preserve_paragraphs: bool,
) -> list[BuiltChunk]:
    """Zerlegt `content` in eine Liste von BuiltChunk (embedding_text + token_count)."""
    content = (content or "").strip()
    if not content:
        return []

    units, mode = _split_into_units(content, preserve_paragraphs)
    units = _expand_oversized(units, target_tokens)
    if not units:
        return []

    packed = _pack_units(units, target_tokens)
    packed = _merge_small_tail(packed, minimum_chunk_tokens)

    overlap_tokens = round(target_tokens * overlap_percent)

    results: list[BuiltChunk] = []
    for i, unit_list in enumerate(packed):
        if i > 0:
            overlap_units = _overlap_prefix(packed[i - 1], overlap_tokens)
            text = _join(overlap_units + unit_list, mode)
        else:
            text = _join(unit_list, mode)

        if include_title and title:
            embedding_text = f"Title: {title}\n\n{text}"
        else:
            embedding_text = text

        results.append(BuiltChunk(embedding_text=embedding_text, token_count=count_tokens(embedding_text)))

    return results
