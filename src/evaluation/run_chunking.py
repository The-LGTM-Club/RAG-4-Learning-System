from __future__ import annotations

import argparse
import json

from src.evaluation.chunking_strategies import list_strategies
from src.indexing import build_chunks, resolve_pdf_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare chunk counts across chunking strategies.")
    parser.add_argument("--path", type=str, default=None, help="PDF path or directory. Defaults to ./data")
    args = parser.parse_args()

    pdf_paths = resolve_pdf_paths(args.path)
    results = []
    for strategy in list_strategies():
        chunks = build_chunks(
            pdf_paths,
            chunk_size=strategy.chunk_size,
            chunk_overlap=strategy.chunk_overlap,
            separators=strategy.separators,
        )
        results.append(
            {
                "strategy": strategy.name,
                "chunk_size": strategy.chunk_size,
                "chunk_overlap": strategy.chunk_overlap,
                "pdf_count": len(pdf_paths),
                "chunk_count": len(chunks),
            }
        )

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
