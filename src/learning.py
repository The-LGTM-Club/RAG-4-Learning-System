from __future__ import annotations

from pydantic import ValidationError

from src.config import get_settings
from src.filters import extract_source_markers
from src.llm import invoke_text, parse_json_object, render_prompt
from src.rag import build_prompt_sources, format_citations, retrieve
from src.schemas import Flashcard, FlashcardSet, QuizItem, QuizSet, Summary


def summarize(
    query: str,
    k: int | None = None,
    filename: str | None = None,
    template_name: str = "summary_query.jinja2",
) -> Summary:
    settings = get_settings()
    chunks = retrieve(
        query,
        k=k or settings.summarize_retrieval_k,
        filename=filename,
    )
    if not chunks:
        return Summary(
            scope="query",
            target=query,
            summary="",
            key_points=[],
            citations=[],
        )

    prompt = render_prompt(
        template_name,
        query=query,
        sources=build_prompt_sources(chunks, include_locations=True),
    )
    payload = parse_json_object(invoke_text(prompt))
    return Summary(
        scope="query",
        target=query,
        summary=str(payload.get("summary", "")).strip(),
        key_points=[str(item).strip() for item in payload.get("key_points", []) if str(item).strip()],
        citations=format_citations(chunks),
    )


def generate_quiz(
    query: str,
    count: int | None = None,
    filename: str | None = None,
) -> QuizSet:
    settings = get_settings()
    total = count or settings.quiz_default_count
    chunks = retrieve(
        query,
        k=settings.generation_retrieval_k,
        filename=filename,
    )
    if not chunks:
        return QuizSet(
            scope="query",
            target=query,
            items=[],
            citations=[],
        )

    prompt = render_prompt(
        "quiz.jinja2",
        query=query,
        count=total,
        sources=build_prompt_sources(chunks, include_locations=True),
    )
    payload = parse_json_object(invoke_text(prompt))

    items: list[QuizItem] = []
    for raw_item in payload.get("items", []):
        candidate = dict(raw_item)
        if "source_markers" not in candidate:
            candidate["source_markers"] = extract_source_markers(candidate.get("explanation", ""))
        try:
            items.append(QuizItem(**candidate))
        except ValidationError:
            continue

    return QuizSet(
        scope="query",
        target=query,
        items=items,
        citations=format_citations(chunks),
    )


def generate_flashcards(
    query: str,
    count: int | None = None,
    filename: str | None = None,
) -> FlashcardSet:
    settings = get_settings()
    total = count or settings.flashcards_default_count
    chunks = retrieve(
        query,
        k=settings.generation_retrieval_k,
        filename=filename,
    )
    if not chunks:
        return FlashcardSet(
            scope="query",
            target=query,
            cards=[],
            citations=[],
        )

    prompt = render_prompt(
        "flashcards.jinja2",
        query=query,
        count=total,
        sources=build_prompt_sources(chunks, include_locations=True),
    )
    payload = parse_json_object(invoke_text(prompt))

    cards: list[Flashcard] = []
    for raw_card in payload.get("cards", []):
        candidate = dict(raw_card)
        if "source_markers" not in candidate:
            marker_source = " ".join(
                str(candidate.get(field, ""))
                for field in ("front", "back", "hint")
            )
            candidate["source_markers"] = extract_source_markers(marker_source)
        try:
            cards.append(Flashcard(**candidate))
        except ValidationError:
            continue

    return FlashcardSet(
        scope="query",
        target=query,
        cards=cards,
        citations=format_citations(chunks),
    )
