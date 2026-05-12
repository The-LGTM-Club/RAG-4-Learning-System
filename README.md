# NotebookLM RAG

This repository is the notebook-to-package refactor of the original local NotebookLM experiments. The combined logic from the source notebooks now lives in `src/`, the PDFs are in `data/`, and the Qdrant storage directory is ready under `storage/qdrant/`.

## Structure

```text
data/                  PDF corpus
src/
  prompts/             Jinja prompt templates
  interfaces/          FastAPI, Typer CLI, Gradio UI
  evaluation/          Benchmark CSV and evaluation scripts
  config.py            Runtime settings
  schemas.py           Pydantic models
  indexing.py          PDF loading and chunk ingestion
  store.py             Embeddings and Qdrant helpers
  rag.py               Retrieval and grounded answering
  learning.py          Summary, quiz, flashcards
  llm.py               Model provider and prompt rendering
  filters.py           Text cleanup and retrieval filters
  export.py            Markdown and JSON export helpers
storage/qdrant/        Local vector database files
```

The original notebook sources are still kept in `data-code/` as a migration archive.

## Quick Start

```bash
pip install -r requirements.txt
python -m src.interfaces.cli ingest
python -m src.interfaces.cli answer "What is the main content of this document?"
python -m src.interfaces.cli serve-ui
```

## API

```bash
python -m src.interfaces.cli serve-api
```

Main endpoints:

- `GET /health`
- `POST /ingest`
- `POST /answer`
- `POST /summary`
- `POST /quiz`
- `POST /flashcards`

## Evaluation

```bash
python -m src.evaluation.run_chunking
python -m src.evaluation.run_reranking --limit 10
python -m src.evaluation.ragas_evaluator --limit 10
```
