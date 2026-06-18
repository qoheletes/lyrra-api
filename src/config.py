import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    database_url: str = field(default_factory=lambda: os.environ["DATABASE_URL"])
    r2_account_id: str = field(default_factory=lambda: os.getenv("R2_ACCOUNT_ID", ""))
    r2_bucket: str = field(default_factory=lambda: os.getenv("R2_BUCKET", ""))
    r2_access_key_id: str = field(default_factory=lambda: os.getenv("R2_ACCESS_KEY_ID", ""))
    r2_secret_access_key: str = field(default_factory=lambda: os.getenv("R2_SECRET_ACCESS_KEY", ""))
    r2_public_url: str = field(default_factory=lambda: os.getenv("R2_PUBLIC_URL", ""))
    openai_api_key: str = field(default_factory=lambda: os.environ["OPENAI_API_KEY"])
    youtube_api_key: str = field(default_factory=lambda: os.environ["YOUTUBE_API_KEY"])
    yt_dlp_cookies_file: str = field(default_factory=lambda: os.getenv("YT_DLP_COOKIES_FILE", ""))
    jwt_secret: str = field(default_factory=lambda: os.environ["JWT_SECRET"])
    jwt_alg: str = field(default_factory=lambda: os.getenv("JWT_ALG", "HS256"))
    access_token_ttl_min: int = field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_TTL_MIN", "60"))
    )


settings = Settings()
