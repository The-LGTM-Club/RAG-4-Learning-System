from __future__ import annotations

import re
import unicodedata

from src.schemas import RetrievedChunk


def clean_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text or "")
    normalized = "".join(
        char
        for char in normalized
        if not unicodedata.category(char).startswith("C") or char in "\n\t"
    )
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def filename_matches(candidate: str, requested: str) -> bool:
    return requested.lower() in candidate.lower()


def filter_chunks(
    chunks: list[RetrievedChunk],
    filename: str | None = None,
) -> list[RetrievedChunk]:
    if not filename:
        return chunks
    return [chunk for chunk in chunks if filename_matches(chunk.metadata.filename, filename)]


def unique_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    seen: set[str] = set()
    deduped: list[RetrievedChunk] = []
    for chunk in chunks:
        if chunk.metadata.chunk_id in seen:
            continue
        deduped.append(chunk)
        seen.add(chunk.metadata.chunk_id)
    return deduped


def extract_source_markers(text: str) -> list[str]:
    markers = re.findall(r"\[S\d+\]", text or "")
    return sorted(set(markers), key=markers.index)
