from typing import Protocol


class EmbeddingProvider(Protocol):
    @property
    def dimension(self) -> int: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
