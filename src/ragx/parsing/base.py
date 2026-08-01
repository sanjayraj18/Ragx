from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class BlockType(StrEnum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    CODE = "code"


# for one block
@dataclass(frozen=True, slots=True)
class ParsedBlock:
    text: str
    type: BlockType = BlockType.PARAGRAPH
    page: int | None = None
    heading_level: int | None = None


# for one document
@dataclass(frozen=True, slots=True)
class ParsedDocument:
    blocks: list[ParsedBlock]

    @property
    def block_count(self) -> int:
        return len(self.blocks)


# same like the storage
class Parser(Protocol):
    def parse(self, data: bytes) -> ParsedDocument: ...
