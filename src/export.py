from __future__ import annotations

import json
from pathlib import Path

from src.schemas import AnswerResponse, FlashcardSet, QuizSet, Summary


def answer_to_markdown(result: AnswerResponse) -> str:
    lines = [result.answer.strip(), "", "## Citations"]
    if not result.citations:
        lines.append("- None")
        return "\n".join(lines)

    for citation in result.citations:
        lines.append(
            f"- [{citation.source_marker}] {citation.filename} (page {citation.page})"
        )
    return "\n".join(lines)


def summary_to_markdown(result: Summary) -> str:
    lines = [result.summary.strip() or "_No summary generated._", "", "## Key Points"]
    if result.key_points:
        lines.extend(f"- {point}" for point in result.key_points)
    else:
        lines.append("- None")

    lines.extend(["", "## Citations"])
    if result.citations:
        lines.extend(
            f"- [{citation.source_marker}] {citation.filename} (page {citation.page})"
            for citation in result.citations
        )
    else:
        lines.append("- None")
    return "\n".join(lines)


def quiz_to_markdown(result: QuizSet) -> str:
    lines = []
    for index, item in enumerate(result.items, start=1):
        lines.append(f"## Question {index}")
        lines.append(item.question)
        lines.extend(
            f"- {option}" if option_index != item.correct_index else f"- {option} <- correct"
            for option_index, option in enumerate(item.options)
        )
        lines.append(f"Explanation: {item.explanation}")
        if item.topic:
            lines.append(f"Topic: {item.topic}")
        if item.difficulty:
            lines.append(f"Difficulty: {item.difficulty}")
        lines.append("")

    if not lines:
        lines.append("_No quiz items generated._")
    return "\n".join(lines).strip()


def flashcards_to_markdown(result: FlashcardSet) -> str:
    lines = []
    for index, card in enumerate(result.cards, start=1):
        lines.append(f"## Card {index}")
        lines.append(f"Front: {card.front}")
        lines.append(f"Back: {card.back}")
        if card.hint:
            lines.append(f"Hint: {card.hint}")
        if card.topic:
            lines.append(f"Topic: {card.topic}")
        if card.source_markers:
            lines.append(f"Sources: {', '.join(card.source_markers)}")
        lines.append("")

    if not lines:
        lines.append("_No flashcards generated._")
    return "\n".join(lines).strip()


def to_json(data: AnswerResponse | Summary | QuizSet | FlashcardSet) -> str:
    return json.dumps(data.model_dump(), ensure_ascii=False, indent=2)


def write_text(content: str, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
