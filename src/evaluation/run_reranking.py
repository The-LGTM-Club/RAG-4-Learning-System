from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher

from src.config import get_settings
from src.evaluation.ragas_evaluator import load_benchmark
from src.rag import answer_from_chunks, retrieve
from src.schemas import RetrievedChunk


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def similarity_score(left: str, right: str) -> float:
    return SequenceMatcher(a=_normalize(left), b=_normalize(right)).ratio()


def rerank_chunks(
    query: str,
    chunks: list[RetrievedChunk],
    model_name: str,
    top_n: int,
) -> list[RetrievedChunk]:
    from sentence_transformers import CrossEncoder

    model = CrossEncoder(model_name)
    pairs = [(query, chunk.text) for chunk in chunks]
    scores = model.predict(pairs)
    ranked = sorted(
        zip(chunks, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )
    return [chunk for chunk, _ in ranked[:top_n]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare baseline retrieval against cross-encoder reranking.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--pool-size", type=int, default=12)
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--filename", type=str, default=None)
    args = parser.parse_args()

    settings = get_settings()
    benchmark = load_benchmark().head(args.limit)

    baseline_scores: list[float] = []
    reranked_scores: list[float] = []
    details = []

    for record in benchmark.to_dict(orient="records"):
        question = str(record["question"])
        ground_truth = str(record["ground_truth"])

        pool = retrieve(question, k=args.pool_size, filename=args.filename, fetch_multiplier=1)
        baseline_chunks = pool[: args.top_n]
        reranked_chunks = rerank_chunks(
            question,
            pool,
            model_name=settings.reranker_model,
            top_n=args.top_n,
        )

        baseline_answer = answer_from_chunks(question, baseline_chunks).answer
        reranked_answer = answer_from_chunks(question, reranked_chunks).answer

        baseline_score = similarity_score(baseline_answer, ground_truth)
        reranked_score = similarity_score(reranked_answer, ground_truth)
        baseline_scores.append(baseline_score)
        reranked_scores.append(reranked_score)

        details.append(
            {
                "question": question,
                "baseline_score": baseline_score,
                "reranked_score": reranked_score,
            }
        )

    payload = {
        "avg_baseline_score": sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0.0,
        "avg_reranked_score": sum(reranked_scores) / len(reranked_scores) if reranked_scores else 0.0,
        "details": details,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
