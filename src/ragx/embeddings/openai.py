import httpx

from ragx.errors import EmbeddingError, RagxError

_API_URL = "https://api.openai.com/v1/embeddings"
_MAX_BATCH = 512
_DIMENSIONS = {"text-embedding-3-small": 1536, "text-embedding-3-large": 3072}


class OpenAIEmbeddingProvider:
    def __init__(self, model: str, api_key: str) -> None:
        if model not in _DIMENSIONS:
            raise ValueError(f"unknown OpenAI embedding model '{model}'")
        self._model = model
        self._api_key = api_key

    @property
    def dimension(self) -> int:
        return _DIMENSIONS[self._model]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
          vectors: list[list[float]] = []
          async with httpx.AsyncClient(timeout=30.0) as client:
              for start in range(0, len(texts), _MAX_BATCH):
                  batch = texts[start : start + _MAX_BATCH]
                  response = await client.post(
                      _API_URL,
                      headers={"Authorization": f"Bearer {self._api_key}"},
                      json={"model": self._model, "input": batch},
                  )
                  if response.status_code != 200:
                      raise EmbeddingError(
                          f"embedding provider returned {response.status_code}"
                      )
                  items = sorted(response.json()["data"], key=lambda d: d["index"])
                  vectors.extend(item["embedding"] for item in items)
          return vectors
