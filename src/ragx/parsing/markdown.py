"""Markdown: structure is recoverable by line inspection — headings,
fenced code, list items, paragraphs. No library needed; markdown was
designed to be parsed this way."""

import re

from ragx.parsing.base import BlockType, ParsedBlock, ParsedDocument

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+(.*)$")


class MarkdownParser:
    def parse(self, data: bytes) -> ParsedDocument:
        text = data.decode("utf-8", errors="replace")
        blocks: list[ParsedBlock] = []
        paragraph: list[str] = []
        in_code = False
        code: list[str] = []

        def flush_paragraph() -> None:
            if paragraph:
                blocks.append(ParsedBlock(text=" ".join(paragraph)))
                paragraph.clear()

        for line in text.splitlines():
            if line.strip().startswith("```"):
                if in_code:
                    blocks.append(ParsedBlock(text="\n".join(code), type=BlockType.CODE))
                    code.clear()
                else:
                    flush_paragraph()
                in_code = not in_code
                continue
            if in_code:
                code.append(line)
                continue

            if heading := _HEADING.match(line):
                flush_paragraph()
                blocks.append(
                    ParsedBlock(
                        text=heading.group(2).strip(),
                        type=BlockType.HEADING,
                        heading_level=len(heading.group(1)),
                    )
                )
            elif item := _LIST_ITEM.match(line):
                flush_paragraph()
                blocks.append(ParsedBlock(text=item.group(1).strip(), type=BlockType.LIST_ITEM))
            elif not line.strip():
                flush_paragraph()
            else:
                paragraph.append(line.strip())

        flush_paragraph()
        if in_code and code:  # unterminated fence — keep the content anyway
            blocks.append(ParsedBlock(text="\n".join(code), type=BlockType.CODE))
        return ParsedDocument(blocks=blocks)
