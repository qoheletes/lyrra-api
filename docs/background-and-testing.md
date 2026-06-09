# Background Work & Testing

## Background work — BackgroundTasks vs Celery

| Use BackgroundTasks when…                | Use Celery / Arq / RQ when…                |
|------------------------------------------|--------------------------------------------|
| Task is < 1 second                       | Task takes seconds to minutes              |
| Failure can be silently dropped          | You need retries, dead-letter, or visibility|
| Task is in-process (send email, log row) | Task is CPU-heavy or needs a separate pool |
| You don't need scheduling                | You need cron, ETA, or rate limiting       |

```python
from fastapi import BackgroundTasks

@router.post("/signup")
async def signup(data: SignupIn, bg: BackgroundTasks):
    user = await service.create_user(data)
    bg.add_task(send_welcome_email, user.email)   # fire-and-forget, in-process
    return user
```

> BackgroundTasks run **after the response is sent, in the same worker process**. If the
> worker dies, the task is lost. There is no retry. Don't use them for anything you'd
> page on.

## Testing

### Async client from day one

```python
import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_post(client: AsyncClient):
    resp = await client.post("/posts", json={"title": "hi"})
    assert resp.status_code == 201
```

> **Don't** use `async_asgi_testclient` — it's unmaintained. The example above (httpx +
> `ASGITransport`) is the supported path.

### Override dependencies in tests

Don't monkeypatch internals. Use FastAPI's built-in `dependency_overrides`.

```python
from src.auth.dependencies import parse_jwt_data
from src.main import app


def fake_user():
    return {"user_id": "00000000-0000-0000-0000-000000000001"}


@pytest.fixture(autouse=True)
def _override_auth():
    app.dependency_overrides[parse_jwt_data] = fake_user
    yield
    app.dependency_overrides.clear()
```
