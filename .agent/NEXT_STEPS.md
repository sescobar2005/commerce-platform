# NEXT_STEPS.md

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Next Recommended Implementation Unit

**Database sessions and Alembic configuration** — Configure SQLAlchemy session factory (`get_db()` dependency) and Alembic migration environment.

This unit must be completed before any module that requires data persistence (auth, seller, product, order, etc.).

## Dependencies

| Dependency | Status |
|------------|--------|
| Backend directory structure (`back/src/`, `back/tests/`, `back/alembic/`) | Complete |
| Configuration files (`.env.example`, `.gitignore`, `pyproject.toml`, `README.md`) | Complete |
| SQLAlchemy 2.0 database engine configuration | Complete (`back/src/core/database.py`, commit `80b9f59`) |
| Local PostgreSQL instance | Not yet provisioned |
| Alembic configuration | Not yet started |

## Prerequisites (must be in place before implementation)

- Local PostgreSQL installed and running
- Development database created (`plataforma_comercio_dev`)
- `DATABASE_URL` configured in `back/.env`
- SQLAlchemy session factory (`get_db()`) created
- Alembic environment configured (`alembic.ini`, `back/alembic/env.py`)
- RLS policies designed (per `SECURITY.md` row-level security requirement)

## Completion Criteria

- [ ] `back/src/core/database.py` updated with session factory and `get_db()` dependency
- [ ] `back/alembic/env.py` configured for migrations
- [ ] `alembic.ini` present and functional
- [ ] `alembic current` runs without errors
- [ ] Database connection test passes (SELECT 1 against PostgreSQL)
- [ ] RLS policies documented and ready to implement per entity

## Authorization Required

**The user must explicitly approve this implementation task before work begins.** No code will be written until authorization is given.

## Subsequent Units (after database config + sessions)

1. **Authentication module** (auth-module): User model, JWT, Argon2, login/register endpoints
2. **Alembic initial migration**: Create `users` and `sellers` tables
3. **Basic tests**: Authentication and database connection tests
