"""Plain text: the simplest adapter — blank lines separate paragraphs."""

from ragx.parsing.base import BlockType, ParsedBlock, ParsedDocument


class PlainTextParser:
    def parse(self, data: bytes) -> ParsedDocument:
        text = data.decode("utf-8", errors="replace")
        blocks = [
            ParsedBlock(text=paragraph.strip(), type=BlockType.PARAGRAPH)
            for paragraph in text.split("\n\n")
            if paragraph.strip()
        ]

        return ParsedDocument(blocks=blocks)
