from ragx.chunking.base import ChunkDraft
from ragx.parsing.base import BlockType, ParsedDocument


def _split_long(text: str, size: int, overlap: int, separator: str) -> list[str]:
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            cut = text.rfind(separator, start, end)
            if cut > start:
                end = cut
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        start = max(end - overlap, start + 1)
    return pieces


class BlockChunker:
    def chunk(
        self, document: ParsedDocument, *, chunk_size: int, chunk_overlap: int
    ) -> list[ChunkDraft]:
        chunks: list[ChunkDraft] = []
        heading = ""
        parts: list[str] = []
        pages: list[int] = []
        length = 0

        def flush(carry_overlap: bool) -> None:
            nonlocal parts, pages, length
            if not parts:
                return
            body = "\n\n".join(parts)
            text = f"{heading}\n\n{body}" if heading else body
            chunks.append(
                ChunkDraft(
                    position=len(chunks),
                    text=text,
                    page_start=min(pages) if pages else None,
                    page_end=max(pages) if pages else None,
                )
            )
            if carry_overlap and chunk_overlap > 0:
                tail = body[-chunk_overlap:]
                cut = tail.find(" ")
                tail = tail[cut + 1 :] if 0 <= cut < len(tail) - 1 else tail
                parts, length = [tail], len(tail)
            else:
                parts, length = [], 0
            pages = pages[-1:] if pages else []

        for block in document.blocks:
            if block.type is BlockType.HEADING:
                flush(carry_overlap=False)
                heading = block.text
                pages = [block.page] if block.page else []
                continue

            separator = "\n" if block.type in (BlockType.TABLE, BlockType.CODE) else " "
            texts = (
                _split_long(block.text, chunk_size, chunk_overlap, separator)
                if len(block.text) > chunk_size
                else [block.text]
            )
            for text in texts:
                if length + len(text) > chunk_size and parts:
                    flush(carry_overlap=True)
                parts.append(text)
                length += len(text)
                if block.page is not None:
                    pages.append(block.page)

        flush(carry_overlap=False)
        return chunks
