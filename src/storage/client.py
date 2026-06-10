from abc import ABC, abstractmethod

import boto3

from src.config import settings
from src.storage.exceptions import StorageError


class StorageAdapter(ABC):
    @abstractmethod
    def upload(self, key: str, data: bytes) -> str:
        """Upload data and return the public URL."""

    @abstractmethod
    def download(self, key: str) -> bytes | None:
        """Return the raw bytes for key, or None if not found."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete the file at key."""

    @abstractmethod
    def get_public_url(self, key: str) -> str:
        """Return the public URL for a stored key without uploading."""


class R2Adapter(StorageAdapter):
    def __init__(
        self,
        account_id: str,
        bucket: str,
        access_key_id: str,
        secret_access_key: str,
        public_url: str,
    ):
        self._s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )
        self._bucket = bucket
        self._public_url = public_url.rstrip("/")

    def upload(self, key: str, data: bytes) -> str:
        self._s3.put_object(Bucket=self._bucket, Key=key, Body=data)
        return self.get_public_url(key)

    def download(self, key: str) -> bytes | None:
        try:
            response = self._s3.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()
        except self._s3.exceptions.NoSuchKey:
            return None
        except Exception:
            return None

    def delete(self, key: str) -> None:
        self._s3.delete_object(Bucket=self._bucket, Key=key)

    def get_public_url(self, key: str) -> str:
        return f"{self._public_url}/{key}"


def get_storage() -> StorageAdapter:
    required = {
        "R2_ACCOUNT_ID": settings.r2_account_id,
        "R2_BUCKET": settings.r2_bucket,
        "R2_ACCESS_KEY_ID": settings.r2_access_key_id,
        "R2_SECRET_ACCESS_KEY": settings.r2_secret_access_key,
        "R2_PUBLIC_URL": settings.r2_public_url,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise StorageError(f"R2 storage is not configured. Missing: {', '.join(missing)}")
    return R2Adapter(
        account_id=settings.r2_account_id,
        bucket=settings.r2_bucket,
        access_key_id=settings.r2_access_key_id,
        secret_access_key=settings.r2_secret_access_key,
        public_url=settings.r2_public_url,
    )
