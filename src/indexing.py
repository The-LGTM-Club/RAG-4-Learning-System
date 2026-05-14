from __future__ import annotations

import hashlib
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from src.config import get_settings
from src.filters import clean_text
from src.registry import clear_registry, upsert_documents, utc_timestamp
from src.schemas import DocumentRecord
from src.store import delete_chunks_by_source, ensure_collection, get_vector_store

DEFAULT_SEPARATORS = ("\n\n", "\n", ". ", " ", "")


def resolve_pdf_paths(path: str | Path | None = None) -> list[Path]:
    settings = get_settings()
    base_path = Path(path) if path else settings.data_dir
    if base_path.is_file():
        if base_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a PDF file, got: {base_path}")
        return [base_path]
    if not base_path.exists():
        raise FileNotFoundError(f"Path does not exist: {base_path}")
    return sorted(base_path.glob("*.pdf"))


def _file_checksum(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _source_key(path: Path) -> str:
    normalized = str(path.resolve()).lower()
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]


def build_chunks(
    pdf_paths: Sequence[Path],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    separators: Sequence[str] | None = None,
) -> list[Document]:
    chunks, _ = _build_chunks_and_records(
        pdf_paths=pdf_paths,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
    )
    return chunks


def _build_chunks_and_records(
    pdf_paths: Sequence[Path],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    separators: Sequence[str] | None = None,
) -> tuple[list[Document], list[DocumentRecord]]:
    settings = get_settings()
    page_docs: list[Document] = []
    document_details: dict[str, dict[str, object]] = {}

    for path in pdf_paths:
        loader = PyPDFLoader(str(path))
        pages = loader.load()
        checksum = _file_checksum(path)
        source = str(path.resolve())
        source_key = _source_key(path)
        document_id = hashlib.sha1(
            f"{source_key}:{checksum}".encode("utf-8")
        ).hexdigest()[:16]

        for doc in pages:
            doc.page_content = clean_text(doc.page_content)
            doc.metadata = {
                "document_id": document_id,
                "filename": path.name,
                "source": source,
                "page": int(doc.metadata.get("page", 0)) + 1,
            }
        page_docs.extend(pages)
        document_details[document_id] = {
            "document_id": document_id,
            "filename": path.name,
            "source": source,
            "source_key": source_key,
            "checksum": checksum,
            "file_size": path.stat().st_size,
            "page_count": len(pages),
        }

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap if chunk_overlap is not None else settings.chunk_overlap,
        separators=list(separators or DEFAULT_SEPARATORS),
    )
    chunks = splitter.split_documents(page_docs)

    per_doc_counter: dict[str, int] = defaultdict(int)
    per_doc_chunk_count: dict[str, int] = defaultdict(int)
    for chunk in chunks:
        doc_id = chunk.metadata["document_id"]
        index = per_doc_counter[doc_id]
        per_doc_counter[doc_id] += 1
        per_doc_chunk_count[doc_id] += 1
        chunk.metadata["chunk_id"] = f"{doc_id}:{chunk.metadata['page']}:{index}"

    ingested_at = utc_timestamp()
    records = [
        DocumentRecord(
            document_id=document_id,
            filename=str(details["filename"]),
            source=str(details["source"]),
            source_key=str(details["source_key"]),
            checksum=str(details["checksum"]),
            file_size=int(details["file_size"]),
            page_count=int(details["page_count"]),
            chunk_count=per_doc_chunk_count.get(document_id, 0),
            last_ingested_at=ingested_at,
            source_exists=True,
        )
        for document_id, details in document_details.items()
    ]
    return chunks, records


def make_chunk_ids(chunks: Iterable[Document]) -> list[str]:
    return [
        str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.metadata["chunk_id"]))
        for chunk in chunks
    ]


def ingest_paths(
    pdf_paths: Sequence[Path],
    recreate: bool = False,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    separators: Sequence[str] | None = None,
) -> int:
    ensure_collection(recreate=recreate)
    if not pdf_paths:
        return 0
    if recreate:
        clear_registry()

    chunks, records = _build_chunks_and_records(
        pdf_paths,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
    )
    if not chunks:
        return 0

    for record in records:
        deleted_chunks = delete_chunks_by_source(record.source)
        if deleted_chunks:
            logger.info(
                "Removed {} existing chunks for {} before ingest.",
                deleted_chunks,
                record.filename,
            )

    get_vector_store().add_documents(chunks, ids=make_chunk_ids(chunks))
    upsert_documents(records)
    logger.info(
        "Ingested {} chunks from {} PDF files.",
        len(chunks),
        len(pdf_paths),
    )
    return len(chunks)


def save_and_ingest_pdf(file_path: str | Path, recreate: bool = False) -> int:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    return ingest_paths([path], recreate=recreate)


def ingest_data_directory(
    directory: str | Path | None = None,
    recreate: bool = False,
) -> int:
    pdf_paths = resolve_pdf_paths(directory)
    if not pdf_paths:
        logger.warning("No PDF files found for ingestion.")
        return 0
    return ingest_paths(pdf_paths, recreate=recreate)
