from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkingStrategy:
    name: str
    chunk_size: int
    chunk_overlap: int
    separators: tuple[str, ...] = ("\n\n", "\n", ". ", " ", "")


DEFAULT_STRATEGIES: tuple[ChunkingStrategy, ...] = (
    ChunkingStrategy(name="balanced", chunk_size=1000, chunk_overlap=150),
    ChunkingStrategy(name="compact", chunk_size=700, chunk_overlap=100),
    ChunkingStrategy(name="broad", chunk_size=1400, chunk_overlap=220),
)


def list_strategies() -> list[ChunkingStrategy]:
    return list(DEFAULT_STRATEGIES)


def get_strategy(name: str) -> ChunkingStrategy:
    for strategy in DEFAULT_STRATEGIES:
        if strategy.name == name:
            return strategy
    raise KeyError(f"Unknown chunking strategy: {name}")
