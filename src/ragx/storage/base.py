"""The BlobStorage port: the four verbs the app needs for bytes, typed.

A Protocol, not a base class — adapters match it structurally (mypy checks
the shape), never inherit it. Every payload flows as AsyncIterator[bytes]
(chunks), so file size never dictates memory use."""

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class BlobStorage(Protocol):
    async def store(self, key: str, data: AsyncIterator[bytes]) -> None:
        """Persist the chunked stream under `key`, overwriting if present."""
        ...

    def retrieve(self, key: str) -> AsyncIterator[bytes]:
        """Return the object's bytes as a chunked stream. Raises if absent."""
        ...

    async def delete(self, key: str) -> None:
        """Remove the object at `key`. No error if it does not exist."""
        ...

    async def exists(self, key: str) -> bool:
        """True if an object is stored under `key`."""
        ...
