# CURRENT_TASK.md

## Current Task Information

| Field | Value |
|-------|-------|
| Current phase | 1 (Fundamentals) |
| Current task | Database engine configuration (SQLAlchemy 2.0) |
| Objective | Configure centralized SQLAlchemy 2.0 database engine with environment-based connection URL |
| Scope | `back/src/core/config.py`, `back/src/core/database.py` — engine creation only (no sessions, no models, no Alembic) |
| Files involved | `back/src/__init__.py`, `back/src/core/__init__.py`, `back/src/core/config.py`, `back/src/core/database.py` |
| Completed units | Documentation baseline (6 docs), backend directory structure, config files, database engine configuration |
| Pending units | Database sessions, Alembic setup, database models, authentication module, basic tests |
| Verification status | Python syntax verified; import test not possible (dependencies not installed) |
| Last updated | 2026-11-16 |

### Notes

Database engine configuration implemented: `create_db_engine()` factory function, `Base` declarative class, and module-level `engine` instance. Uses `pydantic-settings` for environment-based `DATABASE_URL`. No sessions, models, or Alembic configured yet (per task scope).
