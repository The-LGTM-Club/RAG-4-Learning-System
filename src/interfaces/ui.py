from __future__ import annotations

import gradio as gr

from src.config import get_settings
from src.export import (
    answer_to_markdown,
    flashcards_to_markdown,
    quiz_to_markdown,
    summary_to_markdown,
)
from src.indexing import ingest_data_directory, save_and_ingest_pdf
from src.interfaces.styles import CSS
from src.learning import generate_flashcards, generate_quiz, summarize
from src.rag import answer


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _answer(question: str, filename: str, k: float) -> str:
    result = answer(
        question,
        k=int(k) if k else None,
        filename=_blank_to_none(filename),
    )
    return answer_to_markdown(result)


def _summary(query: str, filename: str, k: float) -> str:
    result = summarize(
        query,
        k=int(k) if k else None,
        filename=_blank_to_none(filename),
    )
    return summary_to_markdown(result)


def _quiz(query: str, filename: str, count: float) -> str:
    result = generate_quiz(
        query,
        count=int(count),
        filename=_blank_to_none(filename),
    )
    return quiz_to_markdown(result)


def _flashcards(query: str, filename: str, count: float) -> str:
    result = generate_flashcards(
        query,
        count=int(count),
        filename=_blank_to_none(filename),
    )
    return flashcards_to_markdown(result)


def _ingest(path: str, use_ocr: bool, ocr_force_all_pages: bool) -> str:
    path = path.strip()
    ocr_enabled = True if use_ocr else None
    force_ocr = True if ocr_force_all_pages else None
    if not path:
        count = ingest_data_directory(
            ocr_enabled=ocr_enabled,
            ocr_force_all_pages=force_ocr,
        )
    elif path.lower().endswith(".pdf"):
        count = save_and_ingest_pdf(
            path,
            ocr_enabled=ocr_enabled,
            ocr_force_all_pages=force_ocr,
        )
    else:
        count = ingest_data_directory(
            path,
            ocr_enabled=ocr_enabled,
            ocr_force_all_pages=force_ocr,
        )
    return f"Ingested {count} chunks."


def build_demo() -> gr.Blocks:
    settings = get_settings()

    with gr.Blocks(title=settings.project_name, css=CSS) as demo:
        gr.Markdown(f"# {settings.project_name}", elem_id="app-title")
        gr.Markdown(
            "A local RAG workspace extracted from the original notebooks into a modular repo."
        )

        with gr.Tab("Ingest"):
            ingest_path = gr.Textbox(
                label="PDF path or directory",
                placeholder="Leave blank to ingest ./data",
            )
            ingest_ocr = gr.Checkbox(
                label="Use OCR fallback for scanned or low-text pages",
                value=False,
            )
            ingest_ocr_force = gr.Checkbox(
                label="OCR every page",
                value=False,
            )
            ingest_button = gr.Button("Ingest", variant="primary")
            ingest_output = gr.Textbox(label="Status", interactive=False)
            ingest_button.click(
                _ingest,
                inputs=[ingest_path, ingest_ocr, ingest_ocr_force],
                outputs=ingest_output,
            )

        with gr.Tab("Answer"):
            answer_question = gr.Textbox(label="Question", lines=3)
            answer_filename = gr.Textbox(
                label="Filename filter",
                placeholder="Optional: only search one PDF",
            )
            answer_k = gr.Slider(1, 20, value=5, step=1, label="Top K")
            answer_button = gr.Button("Generate answer", variant="primary")
            answer_output = gr.Markdown()
            answer_button.click(
                _answer,
                inputs=[answer_question, answer_filename, answer_k],
                outputs=answer_output,
            )

        with gr.Tab("Summary"):
            summary_query = gr.Textbox(label="Summary request", lines=3)
            summary_filename = gr.Textbox(
                label="Filename filter",
                placeholder="Optional: only summarize one PDF",
            )
            summary_k = gr.Slider(1, 32, value=12, step=1, label="Top K")
            summary_button = gr.Button("Generate summary", variant="primary")
            summary_output = gr.Markdown()
            summary_button.click(
                _summary,
                inputs=[summary_query, summary_filename, summary_k],
                outputs=summary_output,
            )

        with gr.Tab("Quiz"):
            quiz_query = gr.Textbox(label="Quiz request", lines=3)
            quiz_filename = gr.Textbox(
                label="Filename filter",
                placeholder="Optional: only use one PDF",
            )
            quiz_count = gr.Slider(1, 10, value=5, step=1, label="Question count")
            quiz_button = gr.Button("Generate quiz", variant="primary")
            quiz_output = gr.Markdown()
            quiz_button.click(
                _quiz,
                inputs=[quiz_query, quiz_filename, quiz_count],
                outputs=quiz_output,
            )

        with gr.Tab("Flashcards"):
            flash_query = gr.Textbox(label="Flashcard request", lines=3)
            flash_filename = gr.Textbox(
                label="Filename filter",
                placeholder="Optional: only use one PDF",
            )
            flash_count = gr.Slider(1, 12, value=5, step=1, label="Card count")
            flash_button = gr.Button("Generate flashcards", variant="primary")
            flash_output = gr.Markdown()
            flash_button.click(
                _flashcards,
                inputs=[flash_query, flash_filename, flash_count],
                outputs=flash_output,
            )

    return demo


if __name__ == "__main__":
    app_settings = get_settings()
    build_demo().launch(
        server_name=app_settings.ui_host,
        server_port=app_settings.ui_port,
        share=app_settings.ui_share,
    )
