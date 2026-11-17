# NEXT_STEPS.md

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Next Recommended Implementation Unit

**Database models** — Define SQLAlchemy declarative models for `users`, `sellers`, and other entities per `DATABASE.md`.

This unit must be completed before Alembic migrations can generate schema changes.

## Dependencies

| Dependency | Status |
|------------|--------|
| Backend directory structure (`back/src/`, `back/tests/`, `back/alembic/`) | Complete |
| Configuration files (`.env.example`, `.gitignore`, `pyproject.toml`, `README.md`) | Complete |
| SQLAlchemy 2.0 database engine configuration | Complete (`back/src/core/database.py`) |
| SQLAlchemy session factory (`SessionLocal`) | Complete (`back/src/core/database.py`, commit `3ea0199`) |
| SQLAlchemy session dependency (`get_db()`) | Complete (`back/src/core/database.py`, commit `667a965`) |
| Alembic migration environment | Complete (`back/alembic.ini`, commit `5d17e69`; `back/alembic/env.py`, commit `23d10dc`) |
| Database unit tests | Complete (`back/tests/test_database_unit.py`, commit `290fb9b`) |
| Database integration tests | Complete (`back/tests/test_database_integration.py`, commit `a768678`) |
| Psycopg 3 driver dependency | Complete (`back/pyproject.toml`, commit `d055846`) |
| Local PostgreSQL instance | Not yet provisioned |

## Prerequisites (must be in place before implementation)

- SQLAlchemy `Base` declarative class available (`back/src/core/database.py`)
- Database engine and session factory configured
- Entity definitions from `DATABASE.md` reviewed
- Local PostgreSQL instance (for integration tests)

## Completion Criteria

- [ ] `back/src/core/models/` directory with model modules
- [ ] User model (users table)
- [ ] Seller model (sellers table)
- [ ] Store model (stores table)
- [ ] All models inherit from `Base`
- [ ] Models use correct column types and constraints per `DATABASE.md`
- [ ] Unit tests for model definitions
- [ ] `alembic revision --autogenerate` works (after models exist)

## Authorization Required

**The user must explicitly approve this implementation task before work begins.** No code will be written until authorization is given.

## Subsequent Units (after database models)

1. **Alembic initial migration**: Create `users` and `sellers` tables via `alembic revision --autogenerate`
2. **Authentication module** (auth-module): User registration, login, JWT, Argon2
3. **Basic tests**: Authentication and database connection tests
