# NotebookLM RAG

This repository is a notebook-to-package refactor of a local NotebookLM-style RAG workflow. The code lives in `src/`, the PDF corpus lives in `data/`, and the vector store is a local embedded Qdrant database under `storage/qdrant/`.

You do not need to run a separate Qdrant server or Docker container for this project.

## Prerequisites

- Python 3.10 or newer
- Internet access on the first run if you use the default local Hugging Face provider
- Enough RAM and disk for model downloads and embeddings

The default configuration loads:

- LLM: `Qwen/Qwen2.5-1.5B-Instruct`
- Embedding model: `keepitreal/vietnamese-sbert`

Those models are downloaded the first time they are used.

## Setup

1. Create a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create a local `.env` file from the example.

```powershell
Copy-Item .env.example .env
```

4. Choose an LLM provider in `.env`.

Default local provider:

```env
NOTEBOOKLM_LLM_PROVIDER=hf_local
NOTEBOOKLM_HF_MODEL=Qwen/Qwen2.5-1.5B-Instruct
NOTEBOOKLM_HF_MAX_NEW_TOKENS=1024
```

Gemini provider:

```env
NOTEBOOKLM_LLM_PROVIDER=gemini
GOOGLE_API_KEY=your-google-api-key
NOTEBOOKLM_GEMINI_MODEL=gemini-2.5-flash
```

Mistral provider:

```env
NOTEBOOKLM_LLM_PROVIDER=mistral
MISTRAL_API_KEY=your-mistral-api-key
NOTEBOOKLM_MISTRAL_MODEL=mistral-small-latest
NOTEBOOKLM_MISTRAL_MAX_TOKENS=1024
```

`NOTEBOOKLM_DATA_DIR` defaults to `data`, and `NOTEBOOKLM_STORAGE_DIR` defaults to `storage/qdrant`.

## Data

Put PDF files in `data/`, or pass a file path or directory path directly to the ingest command.

Examples already included in this repo:

```text
data/
  [Description]-LLMs-Fine-tuning.pdf
  [Description]-Poem-Generation-GPT2.pdf
  [Description]-Pretraining-GPT.pdf
  [Description]-Project-2.2-Text-Classification-Naive-Bayes-Vector-Database.pdf
  [Reading]-LLM-Alignment.pdf
  [Reading]-Reasoning-LLMs.pdf
  [Reading_Quiz]-Question-Answering.pdf
```

## Ingest Documents

Index every PDF in `data/`:

```bash
python -m src.interfaces.cli ingest
```

Index a single PDF:

```bash
python -m src.interfaces.cli ingest "data/[Reading]-LLM-Alignment.pdf"
```

Index a different directory:

```bash
python -m src.interfaces.cli ingest "C:\path\to\pdf-folder"
```

Rebuild the collection from scratch:

```bash
python -m src.interfaces.cli ingest --recreate
```

Use `--recreate` when you want to reset the local vector index after changing the corpus or chunking behavior.

## CLI Usage

Answer a question:

```bash
python -m src.interfaces.cli answer "What is the main content of this document?"
```

Answer from one specific file only:

```bash
python -m src.interfaces.cli answer "What is alignment?" --filename "[Reading]-LLM-Alignment.pdf"
```

Return JSON instead of Markdown:

```bash
python -m src.interfaces.cli answer "What is alignment?" --output json
```

Generate a summary:

```bash
python -m src.interfaces.cli summary "Summarize the main ideas about alignment"
```

Generate a quiz:

```bash
python -m src.interfaces.cli quiz "Create a quiz on reasoning LLMs" --count 5
```

Generate flashcards:

```bash
python -m src.interfaces.cli flashcards "Create flashcards for pretraining GPT" --count 8
```

Available CLI commands:

- `ingest`
- `answer`
- `summary`
- `quiz`
- `flashcards`
- `serve-api`
- `serve-ui`

## Web UI

Start the Gradio interface:

```bash
python -m src.interfaces.cli serve-ui
```

Open:

```text
http://127.0.0.1:7860
```

The default host and port come from:

- `NOTEBOOKLM_UI_HOST`
- `NOTEBOOKLM_UI_PORT`
- `NOTEBOOKLM_UI_SHARE`

## API

Start the FastAPI server:

```bash
python -m src.interfaces.cli serve-api
```

Open:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

Main endpoints:

- `GET /health`
- `POST /ingest`
- `POST /answer`
- `POST /summary`
- `POST /quiz`
- `POST /flashcards`

Example health check:

```bash
curl http://127.0.0.1:8000/health
```

Example ingest request:

```text
curl -X POST http://127.0.0.1:8000/ingest -H "Content-Type: application/json" -d "{\"path\":\"data\",\"recreate\":false}"
```

Example answer request:

```text
curl -X POST http://127.0.0.1:8000/answer -H "Content-Type: application/json" -d "{\"question\":\"What is alignment?\",\"k\":5,\"filename\":\"[Reading]-LLM-Alignment.pdf\"}"
```

Request payloads:

- `/ingest`: `{"path": "optional path", "recreate": false}`
- `/answer`: `{"question": "...", "k": 5, "filename": "optional.pdf"}`
- `/summary`: `{"query": "...", "k": 12, "filename": "optional.pdf"}`
- `/quiz`: `{"query": "...", "count": 5, "filename": "optional.pdf"}`
- `/flashcards`: `{"query": "...", "count": 5, "filename": "optional.pdf"}`

## Evaluation

Run ingestion before evaluation so the local vector store contains the documents you want to test.

Compare chunking strategies:

```bash
python -m src.evaluation.run_chunking
```

Compare baseline retrieval vs reranking:

```bash
python -m src.evaluation.run_reranking --limit 10
```

Run RAGAS evaluation:

```bash
python -m src.evaluation.ragas_evaluator --limit 10
```

Notes:

- `run_reranking` loads the reranker model configured by `NOTEBOOKLM_RERANKER_MODEL` in code defaults.
- `ragas_evaluator` uses the benchmark CSV under `src/evaluation/benchmark_rag.csv`.
- Evaluation commands may download additional models on the first run.

## Important Configuration

The most important environment variables are:

- `NOTEBOOKLM_DATA_DIR`
- `NOTEBOOKLM_STORAGE_DIR`
- `NOTEBOOKLM_QDRANT_COLLECTION`
- `NOTEBOOKLM_CHUNK_SIZE`
- `NOTEBOOKLM_CHUNK_OVERLAP`
- `NOTEBOOKLM_EMBEDDING_MODEL`
- `NOTEBOOKLM_EMBEDDING_DEVICE`
- `NOTEBOOKLM_LLM_PROVIDER`
- `NOTEBOOKLM_LLM_TEMPERATURE`
- `NOTEBOOKLM_HF_MODEL`
- `NOTEBOOKLM_HF_MAX_NEW_TOKENS`
- `GOOGLE_API_KEY`
- `NOTEBOOKLM_GEMINI_MODEL`
- `MISTRAL_API_KEY`
- `NOTEBOOKLM_MISTRAL_MODEL`
- `NOTEBOOKLM_MISTRAL_MAX_TOKENS`
- `NOTEBOOKLM_API_HOST`
- `NOTEBOOKLM_API_PORT`
- `NOTEBOOKLM_RERANKER_MODEL`
- `NOTEBOOKLM_UI_HOST`
- `NOTEBOOKLM_UI_PORT`
- `NOTEBOOKLM_UI_SHARE`

See `.env.example` for the current baseline values, then add provider-specific keys such as `GOOGLE_API_KEY` or `MISTRAL_API_KEY` when needed.

## Repository Structure

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

## Troubleshooting

`ModuleNotFoundError` when running CLI or API:
Install dependencies in the active virtual environment with `pip install -r requirements.txt`.

`No PDF files found for ingestion.`:
Put PDF files in `data/` or pass an explicit file or directory path to `ingest`.

The first run is slow:
This is expected for `hf_local`, because the local LLM and embedding model are downloaded and loaded on demand.

Responses are empty or say no information was found:
Run `python -m src.interfaces.cli ingest` first, or rebuild the collection with `python -m src.interfaces.cli ingest --recreate`.

You want a fully local setup:
Keep `NOTEBOOKLM_LLM_PROVIDER=hf_local` and do not configure Gemini or Mistral keys.
