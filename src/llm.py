from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from langchain_core.messages import HumanMessage
from loguru import logger

from src.config import get_settings


@lru_cache(maxsize=1)
def get_prompt_environment() -> Environment:
    templates_dir = Path(__file__).resolve().parent / "prompts"
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_prompt(template_name: str, **context: Any) -> str:
    template = get_prompt_environment().get_template(template_name)
    return template.render(**context).strip() + "\n"


def _normalize_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return str(content)


@lru_cache(maxsize=1)
def _build_hf_local():
    import torch
    from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

    settings = get_settings()
    logger.info("Loading local Hugging Face model: {}", settings.hf_model)

    tokenizer = AutoTokenizer.from_pretrained(settings.hf_model)

    model_kwargs: dict[str, Any] = {}
    if torch.cuda.is_available():
        model_kwargs["torch_dtype"] = torch.bfloat16
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(
        settings.hf_model,
        **model_kwargs,
    )

    pipeline_kwargs: dict[str, Any] = {
        "task": "text-generation",
        "model": model,
        "tokenizer": tokenizer,
        "max_new_tokens": settings.hf_max_new_tokens,
        "do_sample": settings.llm_temperature > 0,
        "return_full_text": False,
    }
    if settings.llm_temperature > 0:
        pipeline_kwargs["temperature"] = settings.llm_temperature

    text_gen_pipeline = pipeline(**pipeline_kwargs)
    return ChatHuggingFace(llm=HuggingFacePipeline(pipeline=text_gen_pipeline))


@lru_cache(maxsize=1)
def _build_gemini():
    from langchain_google_genai import ChatGoogleGenerativeAI

    settings = get_settings()
    model_kwargs: dict[str, Any] = {
        "model": settings.gemini_model,
        "temperature": settings.llm_temperature,
    }
    if settings.gemini_api_key:
        model_kwargs["google_api_key"] = settings.gemini_api_key

    return ChatGoogleGenerativeAI(
        **model_kwargs,
    )


@lru_cache(maxsize=1)
def _build_mistral():
    from langchain_mistralai.chat_models import ChatMistralAI

    settings = get_settings()
    model_kwargs: dict[str, Any] = {
        "model": settings.mistral_model,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.mistral_max_tokens,
    }
    if settings.mistral_api_key:
        model_kwargs["api_key"] = settings.mistral_api_key

    return ChatMistralAI(**model_kwargs)


@lru_cache(maxsize=1)
def get_llm():
    settings = get_settings()
    if settings.llm_provider == "hf_local":
        return _build_hf_local()
    if settings.llm_provider == "gemini":
        return _build_gemini()
    if settings.llm_provider == "mistral":
        return _build_mistral()
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


def invoke_text(prompt: str) -> str:
    response = get_llm().invoke([HumanMessage(content=prompt)])
    return _normalize_message_content(response.content).strip()


def parse_json_object(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        logger.error("No JSON object found in model output.")
        return {}

    payload = match.group(0)
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON returned by model: {}", exc)
        return {}


def clear_llm_caches() -> None:
    get_prompt_environment.cache_clear()
    _build_hf_local.cache_clear()
    _build_gemini.cache_clear()
    _build_mistral.cache_clear()
    get_llm.cache_clear()
