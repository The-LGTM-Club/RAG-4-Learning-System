from __future__ import annotations

from src.config import get_settings
from src.filters import filter_chunks, unique_chunks
from src.llm import invoke_text, render_prompt
from src.schemas import AnswerResponse, Citation, ChunkMetadata, RetrievedChunk
from src.store import get_vector_store


def retrieve(
    query: str,
    k: int | None = None,
    filename: str | None = None,
    fetch_multiplier: int = 4,
) -> list[RetrievedChunk]:
    settings = get_settings()
    target_k = k or settings.top_k
    raw_k = max(target_k * fetch_multiplier, target_k)

    hits = get_vector_store().similarity_search_with_score(query=query, k=raw_k)
    chunks = [
        RetrievedChunk(
            text=doc.page_content,
            score=float(score),
            metadata=ChunkMetadata(**doc.metadata),
        )
        for doc, score in hits
    ]
    chunks = unique_chunks(chunks)
    chunks = filter_chunks(chunks, filename=filename)
    return chunks[:target_k]


def build_prompt_sources(
    chunks: list[RetrievedChunk],
    include_locations: bool,
) -> list[dict[str, object]]:
    sources: list[dict[str, object]] = []
    for index, chunk in enumerate(chunks, start=1):
        source: dict[str, object] = {
            "marker": f"S{index}",
            "text": chunk.text,
        }
        if include_locations:
            source["filename"] = chunk.metadata.filename
            source["page"] = chunk.metadata.page
        sources.append(source)
    return sources


def format_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    return [
        Citation(
            source_index=index,
            source_marker=f"S{index}",
            filename=chunk.metadata.filename,
            page=chunk.metadata.page,
            section=chunk.metadata.section,
            chunk_id=chunk.metadata.chunk_id,
        )
        for index, chunk in enumerate(chunks, start=1)
    ]


def answer_from_chunks(question: str, chunks: list[RetrievedChunk]) -> AnswerResponse:
    if not chunks:
        return AnswerResponse(
            answer="I could not find information in the documents.",
            citations=[],
        )

    prompt = render_prompt(
        "answer.jinja2",
        question=question,
        sources=build_prompt_sources(chunks, include_locations=False),
    )
    return AnswerResponse(
        answer=invoke_text(prompt),
        citations=format_citations(chunks),
    )


def answer(
    question: str,
    k: int | None = None,
    filename: str | None = None,
) -> AnswerResponse:
    return answer_from_chunks(question, retrieve(question, k=k, filename=filename))
