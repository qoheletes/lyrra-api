import contextlib
from abc import ABC, abstractmethod
from pathlib import Path

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


class LocalFileAdapter(StorageAdapter):
    def __init__(self, base_path: str, public_base: str):
        self._base = Path(base_path)
        self._public_base = public_base.rstrip("/")

    def upload(self, key: str, data: bytes) -> str:
        dest = self._base / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return self.get_public_url(key)

    def download(self, key: str) -> bytes | None:
        target = self._base / key
        if not target.exists():
            return None
        return target.read_bytes()

    def delete(self, key: str) -> None:
        target = self._base / key
        with contextlib.suppress(FileNotFoundError):
            target.unlink()

    def get_public_url(self, key: str) -> str:
        return f"{self._public_base}/{key}"


class S3Adapter(StorageAdapter):
    def __init__(self, bucket: str, region: str, endpoint_url: str | None = None):
        try:
            import boto3

            kwargs = {"region_name": region}
            if endpoint_url:
                kwargs["endpoint_url"] = endpoint_url
            self._s3 = boto3.client("s3", **kwargs)
            self._bucket = bucket
            self._region = region
            self._endpoint_url = endpoint_url
        except ImportError as exc:
            raise StorageError("boto3 is required for S3 storage. Run: pip install boto3") from exc

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
        return f"https://{self._bucket}.s3.{self._region}.amazonaws.com/{key}"


class R2Adapter(S3Adapter):
    def __init__(
        self,
        account_id: str,
        bucket: str,
        access_key_id: str,
        secret_access_key: str,
        public_url: str,
    ):
        try:
            import boto3

            self._s3 = boto3.client(
                "s3",
                endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name="auto",
            )
            self._bucket = bucket
            self._public_url = public_url.rstrip("/")
        except ImportError as exc:
            raise StorageError("boto3 is required for R2 storage. Run: pip install boto3") from exc

    def get_public_url(self, key: str) -> str:
        return f"{self._public_url}/{key}"


def get_storage() -> StorageAdapter:
    if settings.storage_backend == "r2":
        return R2Adapter(
            account_id=settings.r2_account_id,
            bucket=settings.r2_bucket,
            access_key_id=settings.r2_access_key_id,
            secret_access_key=settings.r2_secret_access_key,
            public_url=settings.r2_public_url,
        )
    if settings.storage_backend == "s3":
        return S3Adapter(bucket=settings.s3_bucket, region=settings.s3_region)
    return LocalFileAdapter(
        base_path=settings.local_storage_path,
        public_base=settings.local_storage_public_base,
    )
