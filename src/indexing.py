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
from src.store import ensure_collection, get_vector_store

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


def build_chunks(
    pdf_paths: Sequence[Path],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    separators: Sequence[str] | None = None,
) -> list[Document]:
    settings = get_settings()
    page_docs: list[Document] = []

    for path in pdf_paths:
        loader = PyPDFLoader(str(path))
        pages = loader.load()
        document_id = hashlib.sha1(
            f"{path.name}:{path.stat().st_size}".encode("utf-8")
        ).hexdigest()[:16]

        for doc in pages:
            doc.page_content = clean_text(doc.page_content)
            doc.metadata = {
                "document_id": document_id,
                "filename": path.name,
                "source": str(path.resolve()),
                "page": int(doc.metadata.get("page", 0)) + 1,
            }
        page_docs.extend(pages)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap if chunk_overlap is not None else settings.chunk_overlap,
        separators=list(separators or DEFAULT_SEPARATORS),
    )
    chunks = splitter.split_documents(page_docs)

    per_doc_counter: dict[str, int] = defaultdict(int)
    for chunk in chunks:
        doc_id = chunk.metadata["document_id"]
        index = per_doc_counter[doc_id]
        per_doc_counter[doc_id] += 1
        chunk.metadata["chunk_id"] = f"{doc_id}:{chunk.metadata['page']}:{index}"

    return chunks


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

    chunks = build_chunks(
        pdf_paths,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
    )
    if not chunks:
        return 0

    get_vector_store().add_documents(chunks, ids=make_chunk_ids(chunks))
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
