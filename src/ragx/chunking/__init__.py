from ragx.chunking.base import ChunkDraft, Chunker
from ragx.chunking.block_chunker import BlockChunker

__all__ = ["BlockChunker", "ChunkDraft", "Chunker", "default_chunker"]


def default_chunker() -> Chunker:
    return BlockChunker()
