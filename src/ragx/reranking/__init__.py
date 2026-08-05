"""Reranking: the port, adapters, and registry."""

from ragx.config import Settings
from ragx.reranking.base import Reranker
from ragx.reranking.fake import FakeReranker
from ragx.reranking.openai_llm import OpenAILLMReranker

__all__ = ["FakeReranker", "OpenAILLMReranker", "Reranker", "reranker_for"]


def reranker_for(model_id: str, settings: Settings) -> Reranker:
    provider, _, model = model_id.partition("/")
    if provider == "fake":
        return FakeReranker()
    if provider == "openai":
        if settings.openai_api_key is None:
            raise ValueError("RAGX_OPENAI_API_KEY is required for openai reranking")
        return OpenAILLMReranker(model, settings.openai_api_key.get_secret_value())
    raise ValueError(f"unknown reranker provider '{provider}' in '{model_id}'")
