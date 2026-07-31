"""Streaming upload meter: one pass over the byte stream that counts size,
computes the content hash, and yields each chunk onward — O(1) memory.

The size cap is enforced on the ACTUAL bytes as they arrive (never the
client's Content-Length claim), aborting mid-stream the moment it is crossed."""

import hashlib
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from ragx.errors import PayloadTooLargeError

_CHUNK_SIZE = 64 * 1024  # 64 KB — the amount held in RAM at any instant


@dataclass
class UploadMeter:
    max_bytes: int
    size: int = 0
    _hasher: "hashlib._Hash" = field(default_factory=hashlib.sha256)

    async def measure(self, source: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        async for chunk in source:
            self.size += len(chunk)
            if self.size > self.max_bytes:
                raise PayloadTooLargeError(f"upload exceeds the limit of {self.max_bytes} bytes")
            self._hasher.update(chunk)
            yield chunk

    @property
    def content_hash(self) -> str:
        return self._hasher.hexdigest()
