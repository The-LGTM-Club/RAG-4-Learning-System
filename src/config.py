from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="NOTEBOOKLM_",
        extra="ignore",
    )

    project_name: str = "NotebookLM RAG"

    data_dir: Path = Path("data")
    registry_path: Path = Path("storage/document_registry.json")
    storage_dir: Path = Path("storage/qdrant")
    qdrant_collection: str = "rag_chunks"

    chunk_size: int = Field(default=1000, ge=100)
    chunk_overlap: int = Field(default=150, ge=0)
    top_k: int = Field(default=5, ge=1, le=64)

    embedding_model: str = "keepitreal/vietnamese-sbert"
    embedding_device: str = "cpu"
    ocr_enabled: bool = False
    ocr_force_all_pages: bool = False
    ocr_language: str = "eng"
    ocr_dpi: int = Field(default=200, ge=72, le=600)
    ocr_min_characters: int = Field(default=40, ge=0)
    ocr_tesseract_cmd: str | None = None

    llm_provider: Literal["hf_local", "gemini", "mistral"] = "hf_local"
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)

    hf_model: str = "Qwen/Qwen2.5-1.5B-Instruct"
    hf_max_new_tokens: int = Field(default=1024, ge=1)

    gemini_api_key: str | None = Field(default=None, validation_alias="GOOGLE_API_KEY")
    gemini_model: str = "gemini-2.5-flash"

    mistral_api_key: str | None = Field(default=None, validation_alias="MISTRAL_API_KEY")
    mistral_model: str = "mistral-small-latest"
    mistral_max_tokens: int = Field(default=1024, ge=1)

    summarize_retrieval_k: int = Field(default=12, ge=1, le=128)
    generation_retrieval_k: int = Field(default=16, ge=1, le=128)
    quiz_default_count: int = Field(default=5, ge=1, le=50)
    flashcards_default_count: int = Field(default=5, ge=1, le=100)

    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    ui_host: str = "127.0.0.1"
    ui_port: int = Field(default=7860, ge=1, le=65535)
    ui_share: bool = False

    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _ensure_directories(settings: Settings) -> Settings:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.registry_path.parent.mkdir(parents=True, exist_ok=True)
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return _ensure_directories(Settings())
