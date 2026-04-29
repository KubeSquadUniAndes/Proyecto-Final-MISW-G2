import aioboto3  # type: ignore[import-untyped]

from src.domain.services.image_storage_port import ImageStoragePort
from src.infrastructure.config.settings import settings


class S3ImageStorage(ImageStoragePort):
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        session = aioboto3.Session()
        async with session.client("s3", region_name=settings.AWS_REGION) as s3:
            await s3.put_object(
                Bucket=settings.S3_BUCKET,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        return (
            f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        )

    async def delete(self, key: str) -> None:
        session = aioboto3.Session()
        async with session.client("s3", region_name=settings.AWS_REGION) as s3:
            await s3.delete_object(Bucket=settings.S3_BUCKET, Key=key)
