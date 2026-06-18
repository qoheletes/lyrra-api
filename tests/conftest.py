"""Test bootstrap: provide safe env defaults so `src.config` imports without a real .env."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("YOUTUBE_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret")
