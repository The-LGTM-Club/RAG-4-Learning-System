from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from src.rag import answer_from_chunks, retrieve

BENCHMARK_PATH = Path(__file__).resolve().parent / "benchmark_rag.csv"


def _normalize_column(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    return normalized.strip("_")


def load_benchmark(path: str | Path | None = None) -> pd.DataFrame:
    csv_path = Path(path) if path else BENCHMARK_PATH
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1258", "latin-1"):
        try:
            frame = pd.read_csv(csv_path, encoding=encoding)
            frame.columns = [_normalize_column(column) for column in frame.columns]
            if "ground_truth" not in frame.columns and "ground_truth_" in frame.columns:
                frame = frame.rename(columns={"ground_truth_": "ground_truth"})
            return frame
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Unable to read benchmark CSV: {csv_path}") from last_error


def collect_predictions(
    limit: int | None = None,
    k: int | None = None,
    filename: str | None = None,
) -> list[dict[str, Any]]:
    benchmark = load_benchmark()
    if limit:
        benchmark = benchmark.head(limit)

    rows: list[dict[str, Any]] = []
    for record in benchmark.to_dict(orient="records"):
        question = str(record["question"])
        chunks = retrieve(question, k=k, filename=filename)
        prediction = answer_from_chunks(question, chunks)
        rows.append(
            {
                "question": question,
                "answer": prediction.answer,
                "contexts": [chunk.text for chunk in chunks],
                "ground_truth": str(record["ground_truth"]),
            }
        )
    return rows


def evaluate_with_ragas(records: list[dict[str, Any]]) -> Any:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_recall, faithfulness

    dataset = Dataset.from_list(records)
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_recall],
    )
    if hasattr(result, "to_pandas"):
        return result.to_pandas().to_dict(orient="records")
    if hasattr(result, "items"):
        return dict(result.items())
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation on the benchmark CSV.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--filename", type=str, default=None)
    args = parser.parse_args()

    records = collect_predictions(limit=args.limit, k=args.top_k, filename=args.filename)
    scores = evaluate_with_ragas(records)
    print(json.dumps(scores, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
