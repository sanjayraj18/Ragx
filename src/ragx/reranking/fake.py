"""Deterministic fake: Jaccard word overlap between query and text.

No network, no cost — and unlike the embedding fake, its orderings are
semantically plausible (shared words are a real, crude relevance signal),
so funnel behavior is observable offline."""

import re

_WORD = re.compile(r"[a-z0-9]+")


class FakeReranker:
    async def rerank(self, query: str, texts: list[str]) -> list[float]:
        query_words = set(_WORD.findall(query.lower()))
        scores: list[float] = []
        for text in texts:
            words = set(_WORD.findall(text.lower()))
            union = query_words | words
            scores.append(len(query_words & words) / len(union) if union else 0.0)
        return scores
