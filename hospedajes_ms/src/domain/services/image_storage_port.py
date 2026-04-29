from abc import ABC, abstractmethod


class ImageStoragePort(ABC):
    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        """Upload file to storage and return its public URL."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete file from storage by key."""
        ...
