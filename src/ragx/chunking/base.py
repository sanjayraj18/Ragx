from dataclasses import dataclass
from typing import Protocol

from ragx.parsing.base import ParsedDocument


@dataclass(frozen=True, slots=True)
class ChunkDraft:
    position: int
    text: str
    page_start: int | None = None
    page_end: int | None = None


class Chunker(Protocol):
    def chunk(self, document: ParsedDocument, *, chunk_size: int, chunk_overlap: int) -> list[ChunkDraft]: ...