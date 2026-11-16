# NEXT_STEPS.md

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Next Recommended Implementation Unit

**Database configuration** — Configure SQLAlchemy connection, Alembic migrations, and PostgreSQL RLS policies.

This unit must be completed before any module that requires data persistence (auth, seller, product, order, etc.).

## Dependencies

| Dependency | Status |
|------------|--------|
| Backend directory structure (`back/src/`, `back/tests/`, `back/alembic/`) | Complete |
| Configuration files (`.env.example`, `.gitignore`, `pyproject.toml`, `README.md`) | Complete |
| Local PostgreSQL instance | Not yet provisioned |
| SQLAlchemy 2.0 connection setup | Not yet started |
| Alembic configuration | Not yet started |

## Prerequisites (must be in place before implementation)

- PostgreSQL installed and running locally
- Development database created (`plataforma_comercio_dev`)
- `DATABASE_URL` configured in `back/.env`
- SQLAlchemy engine and session factory created
- Alembic environment configured
- RLS policies designed (per `SECURITY.md` row-level security requirement)

## Completion Criteria

- [ ] `back/src/core/database.py` created with SQLAlchemy engine and `get_db()` dependency
- [ ] `back/alembic/env.py` configured for migrations
- [ ] `alembic.ini` present and functional
- [ ] `alembic current` runs without errors
- [ ] Database connection test passes (SELECT 1 against PostgreSQL)
- [ ] RLS policies documented and ready to implement per entity

## Authorization Required

**The user must explicitly approve this implementation task before work begins.** No code will be written until authorization is given.

## Subsequent Units (after database config)

1. **Authentication module** (auth-module): User model, JWT, Argon2, login/register endpoints
2. **Alembic initial migration**: Create `users` and `sellers` tables
3. **Basic tests**: Authentication and database connection tests
