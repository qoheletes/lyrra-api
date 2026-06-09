import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    database_url: str = field(default_factory=lambda: os.environ["DATABASE_URL"])
    storage_backend: str = field(default_factory=lambda: os.getenv("STORAGE_BACKEND", "local"))
    local_storage_path: str = field(
        default_factory=lambda: os.getenv("LOCAL_STORAGE_PATH", "./data/subtitles")
    )
    local_storage_public_base: str = field(
        default_factory=lambda: os.getenv(
            "LOCAL_STORAGE_PUBLIC_BASE", "http://localhost:8000/files"
        )
    )
    s3_bucket: str = field(default_factory=lambda: os.getenv("S3_BUCKET", ""))
    s3_region: str = field(default_factory=lambda: os.getenv("S3_REGION", "us-east-1"))
    r2_account_id: str = field(default_factory=lambda: os.getenv("R2_ACCOUNT_ID", ""))
    r2_bucket: str = field(default_factory=lambda: os.getenv("R2_BUCKET", ""))
    r2_access_key_id: str = field(default_factory=lambda: os.getenv("R2_ACCESS_KEY_ID", ""))
    r2_secret_access_key: str = field(default_factory=lambda: os.getenv("R2_SECRET_ACCESS_KEY", ""))
    r2_public_url: str = field(default_factory=lambda: os.getenv("R2_PUBLIC_URL", ""))
    openai_api_key: str = field(default_factory=lambda: os.environ["OPENAI_API_KEY"])
    youtube_api_key: str = field(default_factory=lambda: os.environ["YOUTUBE_API_KEY"])
    yt_dlp_cookies_file: str = field(default_factory=lambda: os.getenv("YT_DLP_COOKIES_FILE", ""))


settings = Settings()
