# Session Progress Log

## Current State

**Last Updated:** 2026-06-10
**Active Feature:** Refactor `src/` to the flat, domain-organized layout in `docs/`

## Status

### What's Done

- [x] Migrated the package from a hexagonal layout (`{domain}/domain|application|infrastructure/`)
      to the flat, domain-scoped layout mandated by `docs/project-structure.md`.
- [x] Moved shared infra to top level: `src/config.py`, `src/database.py`, `src/storage/`
      (was `src/core/...`). Fixed all imports from `app.*` → `src.*`.
- [x] Collapsed the redundant domain-dataclass layer in `videos`/`subtitles`: services now
      return ORM rows and routers hydrate them with `Schema.model_validate(...)`
      (SQL → ORM → Pydantic, per `docs/auth-and-database.md`). HTTP output unchanged.
- [x] `youtube`: split into `service.py` (ports + use cases + `build_sentences`) and
      `client.py` (yt-dlp / Whisper / OpenAI / search adapters). Use-case class names and
      `build_sentences` preserved (tests depend on them).
- [x] Safe modernizations: `Annotated[...]` route deps, builtin generics + `X | None`
      (ruff `--fix`), `contextlib.suppress`. Updated `pyproject` (`packages=["src"]`,
      `target-version="py310"`), `init.sh` (`ruff check src tests`), `alembic/env.py`, tests.
- [x] Deleted the orphan `src/youtube/service.py` stub and stale hexagonal dirs/pycache.
- [x] Rewrote the three per-domain `ARCHITECTURE.md` files for the flat layout.

### Verification Evidence

- `uv run ruff check src tests` → All checks passed
- `uv run ruff format --check src tests` → 30 files already formatted
- `uv run pytest` → 9 passed, 8 skipped (skips are fixture-gated: `data/transcriptions/*.json` absent)
- `import src.main` + `configure_mappers()` → mappers configure, 12 routes registered

## Notes for Next Session

- **Deferred (needs a dependency):** `docs/pydantic.md` wants config as `BaseSettings`
  (per-domain). Left `src/config.py` as the existing `Settings` dataclass because
  `pydantic-settings` is not installed and scope was "no new deps". Revisit if that changes.
- **Deferred (higher risk):** `docs` favor async SQLAlchemy (`AsyncSession`, async routes).
  Current code is sync (`psycopg2` + `Session`). A migration would touch every route + the
  service layer and needs `asyncpg` + DB integration tests, which don't exist yet.
- The cross-domain ORM imports stay under `TYPE_CHECKING` (circular import); `relationship("…")`
  string args resolve via SQLAlchemy's registry. `datetime` imports carry `# noqa: TC003`
  because `Mapped[datetime]` is de-stringified at mapper-config time and needs the runtime name.
