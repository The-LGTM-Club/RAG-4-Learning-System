from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from src.config import get_settings
from src.documents import (
    delete_registered_document,
    list_registered_documents,
    reingest_registered_document,
)
from src.export import (
    answer_to_markdown,
    delete_document_to_markdown,
    documents_to_markdown,
    flashcards_to_markdown,
    quiz_to_markdown,
    reingest_document_to_markdown,
    summary_to_markdown,
    to_json,
)
from src.indexing import ingest_data_directory, save_and_ingest_pdf
from src.learning import generate_flashcards, generate_quiz, summarize
from src.rag import answer

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _emit(text: str) -> None:
    typer.echo(text)


def _normalize_output(output: str) -> str:
    return output.lower().strip()


@app.command()
def ingest(
    path: Optional[str] = typer.Argument(default=None),
    recreate: bool = typer.Option(False, help="Recreate the Qdrant collection before ingesting."),
) -> None:
    input_path = Path(path) if path else None
    if input_path and input_path.is_file():
        count = save_and_ingest_pdf(input_path, recreate=recreate)
    else:
        count = ingest_data_directory(input_path, recreate=recreate)
    _emit(json.dumps({"ingested_chunks": count}, ensure_ascii=False, indent=2))


@app.command(name="documents")
def documents_cmd(
    output: str = typer.Option("markdown", help="markdown or json"),
) -> None:
    result = list_registered_documents()
    if _normalize_output(output) == "json":
        _emit(to_json(result))
        return
    _emit(documents_to_markdown(result))


@app.command(name="delete-document")
def delete_document_cmd(
    document_id: str = typer.Argument(...),
    output: str = typer.Option("markdown", help="markdown or json"),
) -> None:
    result = delete_registered_document(document_id)
    if _normalize_output(output) == "json":
        _emit(to_json(result))
        return
    _emit(delete_document_to_markdown(result))


@app.command(name="reingest-document")
def reingest_document_cmd(
    document_id: str = typer.Argument(...),
    output: str = typer.Option("markdown", help="markdown or json"),
) -> None:
    result = reingest_registered_document(document_id)
    if _normalize_output(output) == "json":
        _emit(to_json(result))
        return
    _emit(reingest_document_to_markdown(result))


@app.command(name="answer")
def answer_cmd(
    question: str = typer.Argument(...),
    filename: Optional[str] = typer.Option(None, help="Filter chunks by filename."),
    k: Optional[int] = typer.Option(None, min=1),
    output: str = typer.Option("markdown", help="markdown or json"),
) -> None:
    result = answer(question, k=k, filename=filename)
    if _normalize_output(output) == "json":
        _emit(to_json(result))
        return
    _emit(answer_to_markdown(result))


@app.command(name="summary")
def summary_cmd(
    query: str = typer.Argument(...),
    filename: Optional[str] = typer.Option(None, help="Filter chunks by filename."),
    k: Optional[int] = typer.Option(None, min=1),
    output: str = typer.Option("markdown", help="markdown or json"),
) -> None:
    result = summarize(query, k=k, filename=filename)
    if _normalize_output(output) == "json":
        _emit(to_json(result))
        return
    _emit(summary_to_markdown(result))


@app.command(name="quiz")
def quiz_cmd(
    query: str = typer.Argument(...),
    count: Optional[int] = typer.Option(None, min=1),
    filename: Optional[str] = typer.Option(None, help="Filter chunks by filename."),
    output: str = typer.Option("markdown", help="markdown or json"),
) -> None:
    result = generate_quiz(query, count=count, filename=filename)
    if _normalize_output(output) == "json":
        _emit(to_json(result))
        return
    _emit(quiz_to_markdown(result))


@app.command(name="flashcards")
def flashcards_cmd(
    query: str = typer.Argument(...),
    count: Optional[int] = typer.Option(None, min=1),
    filename: Optional[str] = typer.Option(None, help="Filter chunks by filename."),
    output: str = typer.Option("markdown", help="markdown or json"),
) -> None:
    result = generate_flashcards(query, count=count, filename=filename)
    if _normalize_output(output) == "json":
        _emit(to_json(result))
        return
    _emit(flashcards_to_markdown(result))


@app.command(name="serve-api")
def serve_api() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.interfaces.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


@app.command(name="serve-ui")
def serve_ui() -> None:
    from src.interfaces.ui import build_demo

    settings = get_settings()
    build_demo().launch(
        server_name=settings.ui_host,
        server_port=settings.ui_port,
        share=settings.ui_share,
    )


def run() -> None:
    app()


if __name__ == "__main__":
    run()
