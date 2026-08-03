"""Blob storage: the port (BlobStorage) and its adapters.

Consumers import only BlobStorage — the interface. Concrete adapters
(LocalBlobStorage, later S3BlobStorage) are constructed once in the
app lifespan and injected; nothing above this package names an adapter."""

from ragx.storage.base import BlobStorage
from ragx.storage.local import LocalStorage

__all__ = ["BlobStorage", "LocalStorage"]
