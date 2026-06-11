# AGENTS.md

## Docs Hierarchy
```
docs/
  project-structure.md         -- adding modules/packages, checking dependency version compatibility
  async-routes.md              -- writing or changing route handlers; deciding async def vs def, handling blocking I/O
  dependencies.md              -- writing FastAPI dependencies; Annotated[T, Depends(...)] patterns
  pydantic.md                  -- defining or changing Pydantic schemas, validators, serializers
  auth-and-database.md         -- JWT auth (PyJWT) and SQLAlchemy async session/query patterns
  background-and-testing.md    -- background jobs (BackgroundTasks vs Celery) and writing tests (httpx + ASGITransport)
  migrations-docs-linting.md   -- Alembic migrations, OpenAPI docs conventions, ruff linting setup
  anti-patterns-and-reference.md -- reviewing diffs; checklist of common AI-agent mistakes and their fixes
```
