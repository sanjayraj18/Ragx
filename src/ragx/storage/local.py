import contextlib
from collections.abc import AsyncIterator
from pathlib import Path

import aiofiles
import aiofiles.os

_CHUNK_SIZE = 64 * 1024


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self._root = root

    def _path(self, key: str) -> Path:
        return self._root / key

    async def store(self, key: str, data: AsyncIterator[bytes]) -> None:
        path = self._path(key)
        await aiofiles.os.makedirs(path.parent, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            async for chunk in data:
                await f.write(chunk)

    async def retrieve(self, key: str) -> AsyncIterator[bytes]:
        path = self._path(key)
        async with aiofiles.open(path, "rb") as f:
            while chunk := await f.read(_CHUNK_SIZE):
                yield chunk

    async def delete(self, key: str) -> None:
        with contextlib.suppress(FileNotFoundError):
            await aiofiles.os.remove(self._path(key))

    async def exists(self, key: str) -> bool:
        return await aiofiles.os.path.exists(self._path(key))
