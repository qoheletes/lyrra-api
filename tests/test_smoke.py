"""Smoke tests that prove the test framework itself is configured.

These are the "verifiable test framework" check for the initialization phase
(see ./init.sh). They must never be skipped and must not touch the database,
the network, or any external service — their only job is to prove that pytest
collects and runs tests, and that async support is wired up.
"""


def test_pytest_runs():
    """If this passes, pytest is collecting and executing tests."""
    assert 1 + 1 == 2


async def test_asyncio_mode_configured():
    """pyproject sets `asyncio_mode = "auto"`; running this proves pytest-asyncio is active."""
    assert True
