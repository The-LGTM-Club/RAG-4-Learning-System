from __future__ import annotations

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from src.config import get_settings


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    settings = get_settings()
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": settings.embedding_device},
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(path=str(settings.storage_dir))


def ensure_collection(recreate: bool = False) -> None:
    settings = get_settings()
    client = get_client()

    if recreate and client.collection_exists(settings.qdrant_collection):
        client.delete_collection(settings.qdrant_collection)

    if client.collection_exists(settings.qdrant_collection):
        return

    dimension = len(get_embeddings().embed_query("test"))
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=qmodels.VectorParams(
            size=dimension,
            distance=qmodels.Distance.COSINE,
        ),
    )


def get_vector_store() -> QdrantVectorStore:
    settings = get_settings()
    ensure_collection(recreate=False)
    return QdrantVectorStore(
        client=get_client(),
        collection_name=settings.qdrant_collection,
        embedding=get_embeddings(),
    )


def _source_filter(source: str) -> qmodels.Filter:
    return qmodels.Filter(
        must=[
            qmodels.FieldCondition(
                key="metadata.source",
                match=qmodels.MatchValue(value=source),
            )
        ]
    )


def count_chunks_by_source(source: str) -> int:
    settings = get_settings()
    client = get_client()
    if not client.collection_exists(settings.qdrant_collection):
        return 0
    return int(
        client.count(
            collection_name=settings.qdrant_collection,
            count_filter=_source_filter(source),
            exact=True,
        ).count
    )


def delete_chunks_by_source(source: str) -> int:
    settings = get_settings()
    client = get_client()
    if not client.collection_exists(settings.qdrant_collection):
        return 0

    deleted_chunks = count_chunks_by_source(source)
    if not deleted_chunks:
        return 0

    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=qmodels.FilterSelector(filter=_source_filter(source)),
    )
    return deleted_chunks


def collection_count() -> int:
    settings = get_settings()
    client = get_client()
    if not client.collection_exists(settings.qdrant_collection):
        return 0
    return int(client.count(collection_name=settings.qdrant_collection, exact=True).count)


def clear_store_caches() -> None:
    get_embeddings.cache_clear()
    get_client.cache_clear()
