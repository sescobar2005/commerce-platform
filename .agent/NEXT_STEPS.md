# NEXT_STEPS.md

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Next Recommended Implementation Unit

**Alembic migration configuration** — Configure Alembic migration environment (`alembic.ini`, `back/alembic/env.py`) for database schema versioning.

This unit must be completed before any module that requires database tables (auth, seller, product, order, etc.).

## Dependencies

| Dependency | Status |
|------------|--------|
| Backend directory structure (`back/src/`, `back/tests/`, `back/alembic/`) | Complete |
| Configuration files (`.env.example`, `.gitignore`, `pyproject.toml`, `README.md`) | Complete |
| SQLAlchemy 2.0 database engine configuration | Complete (`back/src/core/database.py`, commit `e6e1fdb`) |
| SQLAlchemy session factory (`SessionLocal`) | Complete (`back/src/core/database.py`, commit `3ea0199`) |
| SQLAlchemy session dependency (`get_db()`) | Complete (`back/src/core/database.py`, commit `667a965`) |
| Database unit tests | Complete (`back/tests/test_database_unit.py`, commit `290fb9b`) |
| Database integration tests | Complete (`back/tests/test_database_integration.py`, commit `a768678`) |
| Psycopg 3 driver dependency | Complete (`back/pyproject.toml`, commit `d055846`) |
| Local PostgreSQL instance | Not yet provisioned |

## Prerequisites (must be in place before implementation)

- Local PostgreSQL installed and running
- Development database created (`plataforma_comercio_dev`)
- `DATABASE_URL` configured in `back/.env`
- Alembic environment configured (`alembic.ini`, `back/alembic/env.py`)
- RLS policies designed (per `SECURITY.md` row-level security requirement)

## Completion Criteria

- [ ] `alembic.ini` present and functional
- [ ] `back/alembic/env.py` configured for migrations with SQLAlchemy target metadata
- [ ] `alembic current` runs without errors
- [ ] `alembic revision --autogenerate` works (after models exist)
- [ ] RLS policies documented and ready to implement per entity

## Authorization Required

**The user must explicitly approve this implementation task before work begins.** No code will be written until authorization is given.

## Subsequent Units (after Alembic)

1. **Database models** (SQLAlchemy declarative models for `users`, `sellers`, etc.)
2. **Alembic initial migration**: Create `users` and `sellers` tables
3. **Authentication module** (auth-module): User model, JWT, Argon2, login/register endpoints
4. **Basic tests**: Authentication and database connection tests
