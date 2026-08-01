"""DOCX: a zip of XML where structure is declared, not inferred.

  Word kept the meaning PDF compiled away — headings say they are headings,
  tables are real objects. The mirror-image price: no pages (pagination in
  Word is a rendering artifact), so page stays None."""

import io

from docx import Document as load_docx
from docx.table import Table
from docx.text.paragraph import Paragraph

from ragx.parsing.base import BlockType, ParsedBlock, ParsedDocument

class DocxParser:
    def parse(self, data: bytes) -> ParsedDocument:
        document = load_docx(io.BytesIO(data))
        blocks: list[ParsedBlock] = []

        for item in document.iter_inner_content():
            if isinstance(item, Paragraph):
                text = item.text.strip()
                if not text:
                    continue
                style = item.style.name if item.style and item.style.name else ""
                if style.startswith("Heading"):
                    suffix = style.split()[-1]
                    level = int(suffix) if suffix.isdigit() else 1
                    blocks.append(
                          ParsedBlock(text=text, type=BlockType.HEADING, heading_level=level)
                      )
                elif style.startswith("List"):
                    blocks.append(ParsedBlock(text=text, type=BlockType.LIST_ITEM))
                else:
                    blocks.append(ParsedBlock(text=text))
            elif isinstance(item, Table):
                rows = [
                    " | ".join(cell.text.strip() for cell in row.cells)
                    for row in item.rows
                  ]
                table_text = "\n".join(row for row in rows if row.strip(" |"))
                if table_text:
                    blocks.append(ParsedBlock(text=table_text, type=BlockType.TABLE))

        return ParsedDocument(blocks=blocks)