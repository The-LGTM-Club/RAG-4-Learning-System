from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.config import get_settings
from src.schemas import DocumentRecord

REGISTRY_VERSION = 1


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_registry() -> dict[str, DocumentRecord]:
    settings = get_settings()
    path = settings.registry_path
    if not path.exists():
        return {}

    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("documents", [])
    registry: dict[str, DocumentRecord] = {}
    for raw_record in records:
        record = DocumentRecord(**raw_record)
        registry[record.source_key] = record
    return registry


def save_registry(registry: dict[str, DocumentRecord]) -> None:
    settings = get_settings()
    settings.registry_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": REGISTRY_VERSION,
        "documents": [
            registry[key].model_dump()
            for key in sorted(registry, key=lambda item: registry[item].filename.lower())
        ],
    }
    settings.registry_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_registry() -> None:
    save_registry({})


def upsert_documents(records: list[DocumentRecord]) -> None:
    registry = load_registry()
    for record in records:
        registry[record.source_key] = record
    save_registry(registry)


def list_documents() -> list[DocumentRecord]:
    documents = []
    for record in load_registry().values():
        documents.append(
            record.model_copy(update={"source_exists": Path(record.source).exists()})
        )
    return sorted(documents, key=lambda record: (record.filename.lower(), record.source.lower()))


def get_document(document_id: str) -> DocumentRecord:
    for record in load_registry().values():
        if record.document_id == document_id:
            return record.model_copy(update={"source_exists": Path(record.source).exists()})
    raise KeyError(f"Document not found: {document_id}")


def get_document_by_source(source: str) -> DocumentRecord:
    source_path = str(Path(source).resolve())
    for record in load_registry().values():
        if record.source == source_path:
            return record.model_copy(update={"source_exists": Path(record.source).exists()})
    raise KeyError(f"Document not found for source: {source_path}")


def remove_document(document_id: str) -> DocumentRecord:
    registry = load_registry()
    for source_key, record in registry.items():
        if record.document_id == document_id:
            removed = registry.pop(source_key)
            save_registry(registry)
            return removed.model_copy(update={"source_exists": Path(removed.source).exists()})
    raise KeyError(f"Document not found: {document_id}")
