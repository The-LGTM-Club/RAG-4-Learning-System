from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    document_id: str
    filename: str
    source: str
    page: int
    chunk_id: str
    section: Optional[str] = None


class RetrievedChunk(BaseModel):
    text: str
    score: float
    metadata: ChunkMetadata


class Citation(BaseModel):
    source_index: int
    source_marker: str
    filename: str
    page: int
    section: Optional[str] = None
    chunk_id: str


class AnswerResponse(BaseModel):
    answer: str
    citations: list[Citation]


class Summary(BaseModel):
    scope: str
    target: Optional[str] = None
    summary: str
    key_points: list[str]
    citations: list[Citation]


class QuizItem(BaseModel):
    question: str
    options: list[str]
    correct_index: int = Field(ge=0)
    explanation: str
    source_markers: list[str]
    difficulty: Optional[str] = None
    topic: Optional[str] = None


class QuizSet(BaseModel):
    scope: str
    target: Optional[str] = None
    items: list[QuizItem]
    citations: list[Citation]


class Flashcard(BaseModel):
    front: str
    back: str
    hint: Optional[str] = None
    topic: Optional[str] = None
    source_markers: list[str]


class FlashcardSet(BaseModel):
    scope: str
    target: Optional[str] = None
    cards: list[Flashcard]
    citations: list[Citation]


class IngestRequest(BaseModel):
    path: Optional[str] = None
    recreate: bool = False


class IngestResponse(BaseModel):
    ingested_chunks: int


class AnswerRequest(BaseModel):
    question: str
    k: Optional[int] = Field(default=None, ge=1)
    filename: Optional[str] = None


class SummaryRequest(BaseModel):
    query: str
    k: Optional[int] = Field(default=None, ge=1)
    filename: Optional[str] = None


class QuizRequest(BaseModel):
    query: str
    count: Optional[int] = Field(default=None, ge=1)
    filename: Optional[str] = None


class FlashcardRequest(BaseModel):
    query: str
    count: Optional[int] = Field(default=None, ge=1)
    filename: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    collection: str
