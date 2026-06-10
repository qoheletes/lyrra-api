"""Storage is R2-only: get_storage() must validate config and never fall back to disk."""

import pytest

from src.storage.client import R2Adapter, get_storage
from src.storage.exceptions import StorageError

R2_SETTINGS = {
    "r2_account_id": "acct",
    "r2_bucket": "bucket",
    "r2_access_key_id": "key",
    "r2_secret_access_key": "secret",
    "r2_public_url": "https://files.example.com/",
}


def _configure_r2(monkeypatch, **overrides):
    from src.config import settings

    for name, value in {**R2_SETTINGS, **overrides}.items():
        monkeypatch.setattr(settings, name, value)


def test_get_storage_returns_r2_adapter(monkeypatch):
    _configure_r2(monkeypatch)
    assert isinstance(get_storage(), R2Adapter)


def test_get_storage_raises_when_r2_unconfigured(monkeypatch):
    _configure_r2(monkeypatch, r2_bucket="", r2_secret_access_key="")
    with pytest.raises(StorageError) as exc_info:
        get_storage()
    assert "R2_BUCKET" in str(exc_info.value)
    assert "R2_SECRET_ACCESS_KEY" in str(exc_info.value)


def test_public_url_strips_trailing_slash(monkeypatch):
    _configure_r2(monkeypatch)
    storage = get_storage()
    assert (
        storage.get_public_url("transcriptions/abc.json")
        == "https://files.example.com/transcriptions/abc.json"
    )
