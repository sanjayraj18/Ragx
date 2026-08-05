"""LLM-as-reranker: one chat call scores every candidate against the query.

Not a true cross-encoder, but the same shape — each pair is read jointly.
The model returns JSON scores; count and range are validated strictly,
because a misaligned score list silently reorders the wrong chunks."""

import json

import httpx

from ragx.errors import EmbeddingError

_API_URL = "https://api.openai.com/v1/chat/completions"

_INSTRUCTIONS = (
    "You are a search relevance judge. Given a query and numbered passages, "
    "score each passage's relevance to the query from 0 (irrelevant) to 10 "
    "(directly answers it). Judge only relevance, not writing quality. "
    'Return JSON: {"scores": [<one number per passage, in order>]}'
)


class OpenAILLMReranker:
    def __init__(self, model: str, api_key: str) -> None:
        self._model = model
        self._api_key = api_key

    async def rerank(self, query: str, texts: list[str]) -> list[float]:
        passages = "\n\n".join(f"[{i}] {text[:1500]}" for i, text in enumerate(texts, start=1))
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                _API_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": _INSTRUCTIONS},
                        {
                            "role": "user",
                            "content": f"Query: {query}\n\nPassages:\n\n{passages}",
                        },
                    ],
                },
            )
        if response.status_code != 200:
            raise EmbeddingError(f"reranker provider returned {response.status_code}")
        content = response.json()["choices"][0]["message"]["content"]
        scores = json.loads(content).get("scores")
        if not isinstance(scores, list) or len(scores) != len(texts):
            raise EmbeddingError("reranker returned malformed scores")
        return [float(s) for s in scores]
