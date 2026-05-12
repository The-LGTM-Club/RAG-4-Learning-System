from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException

from src.config import get_settings
from src.indexing import ingest_data_directory, save_and_ingest_pdf
from src.learning import generate_flashcards, generate_quiz, summarize
from src.rag import answer
from src.schemas import (
    AnswerRequest,
    AnswerResponse,
    FlashcardRequest,
    FlashcardSet,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QuizRequest,
    QuizSet,
    Summary,
    SummaryRequest,
)

settings = get_settings()
app = FastAPI(title=settings.project_name, version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", collection=settings.qdrant_collection)


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest) -> IngestResponse:
    try:
        if payload.path:
            path = Path(payload.path)
            if path.is_dir():
                count = ingest_data_directory(path, recreate=payload.recreate)
            else:
                count = save_and_ingest_pdf(path, recreate=payload.recreate)
        else:
            count = ingest_data_directory(recreate=payload.recreate)
        return IngestResponse(ingested_chunks=count)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/answer", response_model=AnswerResponse)
def answer_endpoint(payload: AnswerRequest) -> AnswerResponse:
    try:
        return answer(payload.question, k=payload.k, filename=payload.filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/summary", response_model=Summary)
def summary_endpoint(payload: SummaryRequest) -> Summary:
    try:
        return summarize(payload.query, k=payload.k, filename=payload.filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/quiz", response_model=QuizSet)
def quiz_endpoint(payload: QuizRequest) -> QuizSet:
    try:
        return generate_quiz(
            payload.query,
            count=payload.count,
            filename=payload.filename,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/flashcards", response_model=FlashcardSet)
def flashcard_endpoint(payload: FlashcardRequest) -> FlashcardSet:
    try:
        return generate_flashcards(
            payload.query,
            count=payload.count,
            filename=payload.filename,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
