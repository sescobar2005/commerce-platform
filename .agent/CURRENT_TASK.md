# CURRENT_TASK.md

## Current Task Information

| Field | Value |
|-------|-------|
| Current phase | 1 (Fundamentals) |
| Current task | Database engine configuration (SQLAlchemy 2.0) — COMPLETE |
| Objective | Configure centralized SQLAlchemy 2.0 database engine with environment-based connection URL, connection pooling, and tests |
| Scope | `back/src/core/config.py`, `back/src/core/database.py`, `back/tests/test_database_unit.py`, `back/tests/test_database_integration.py`, `back/pyproject.toml` |
| Files involved | `back/src/__init__.py`, `back/src/core/__init__.py`, `back/src/core/config.py`, `back/src/core/database.py`, `back/pyproject.toml`, `back/tests/__init__.py`, `back/tests/test_database_unit.py`, `back/tests/test_database_integration.py` |
| Completed units | Documentation baseline (6 docs), backend directory structure, config files, database engine configuration + connection pooling, unit tests, integration tests |
| Pending units | Database sessions, Alembic setup, database models, authentication module |
| Verification status | Python syntax verified for all files; import/runtime tests not possible (dependencies not installed) |
| Last updated | 2026-11-16 |

### Notes

Database engine configuration fully implemented:
- `create_db_engine()` factory with connection pooling (pool_size=5, max_overflow=10, pool_timeout=30, pool_recycle=1800, pool_pre_ping=True)
- `Base` declarative class and module-level `engine` instance
- `pydantic-settings` for env-based `DATABASE_URL`
- `psycopg` (Psycopg 3) driver declared in pyproject.toml (replacing psycopg2-binary)
- Unit tests (test_database_unit.py): 7 tests, no live DB required
- Integration tests (test_database_integration.py): 4 tests, require live PostgreSQL, skipped when DATABASE_URL not set
- No sessions, models, or Alembic configured yet (per task scope)
