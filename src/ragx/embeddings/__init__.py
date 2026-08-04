from ragx.config import Settings
from ragx.embeddings.base import EmbeddingProvider
from ragx.embeddings.openai import OpenAIEmbeddingProvider

EMBEDDING_DIMENSION = 1536

__all__ = ["EMBEDDING_DIMENSION", "EmbeddingProvider", "OpenAIEmbeddingProvider", "provider_for"]


def provider_for(model_id: str, settings: Settings) -> EmbeddingProvider:
    provider, _, model = model_id.partition("/")
    if provider == "openai":
        if settings.openai_api_key is None:
            raise ValueError("RAGX_OPENAI_API_KEY is required for openai embedding models")
        return OpenAIEmbeddingProvider(model, settings.openai_api_key.get_secret_value())
    raise ValueError(f"unknown embedding provider '{provider}' in '{model_id}'")
