from ragx.chunking.base import Chunker, ChunkDraft
from ragx.chunking.block_chunker import BlockChunker

__all__ = ["BlockChunker", "Chunker", "ChunkDraft", "default_chunker"]

def default_chunker() -> Chunker:
    return BlockChunker()