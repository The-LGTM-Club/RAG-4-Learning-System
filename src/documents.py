from __future__ import annotations

from pathlib import Path

from src.indexing import save_and_ingest_pdf
from src.registry import get_document, get_document_by_source, list_documents, remove_document
from src.schemas import (
    DeleteDocumentResponse,
    DocumentRegistryResponse,
    ReingestResponse,
)
from src.store import count_chunks_by_source, delete_chunks_by_source


def list_registered_documents() -> DocumentRegistryResponse:
    return DocumentRegistryResponse(documents=list_documents())


def delete_registered_document(document_id: str) -> DeleteDocumentResponse:
    record = get_document(document_id)
    deleted_chunks = delete_chunks_by_source(record.source)
    removed = remove_document(document_id)
    return DeleteDocumentResponse(document=removed, deleted_chunks=deleted_chunks)


def reingest_registered_document(
    document_id: str,
) -> ReingestResponse:
    record = get_document(document_id)
    source_path = Path(record.source)
    if not source_path.exists():
        raise FileNotFoundError(f"Registered document source not found: {source_path}")

    deleted_chunks = count_chunks_by_source(record.source)
    ingested_chunks = save_and_ingest_pdf(source_path, recreate=False)
    updated_record = get_document_by_source(record.source)
    return ReingestResponse(
        document=updated_record,
        deleted_chunks=deleted_chunks,
        ingested_chunks=ingested_chunks,
    )
