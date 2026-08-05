"""The Reranker port: query + candidate texts in, relevance scores out.

A reranker reads each (query, text) pair jointly — the interaction a
bi-encoder's separate embeddings structurally cannot see. Expensive per
pair, so it runs only on the candidate pool the cheap stages surfaced.
Scores align to input order: result[i] scores texts[i], higher = better."""

from typing import Protocol


class Reranker(Protocol):
    async def rerank(self, query: str, texts: list[str]) -> list[float]: ...
