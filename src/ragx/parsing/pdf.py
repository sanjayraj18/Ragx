import pymupdf

from ragx.parsing.base import BlockType, ParsedBlock, ParsedDocument

_TEXT_BLOCK = 0  # PyMuPDF block type: 0 = text, 1 = image


class PdfParser:
    def parse(self, data: bytes) -> ParsedDocument:
        blocks: list[ParsedBlock] = []
        with pymupdf.open(stream=data, filetype="pdf") as pdf:  # type: ignore[no-untyped-call]
            for page_number, page in enumerate(pdf, start=1):
                for block in page.get_text("blocks"):
                    _x0, _y0, _x1, _y1, text, _block_no, block_type = block
                    if block_type != _TEXT_BLOCK or not text.strip():
                        continue
                    blocks.append(
                        ParsedBlock(
                            text=" ".join(text.split()), type=BlockType.PARAGRAPH, page=page_number
                        )
                    )

        return ParsedDocument(blocks=blocks)
