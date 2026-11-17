# NEXT_STEPS.md

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Next Recommended Implementation Unit

**Alembic initial migration** — Generate and apply the first database migration for `users`, `sellers`, `stores`, `categories`, and `products` tables using `alembic revision --autogenerate`.

This unit must be completed before any module that requires database tables (auth, seller, product, order, etc.).

## Dependencies

| Dependency | Status |
|------------|--------|
| Backend directory structure (`back/src/`, `back/tests/`, `back/alembic/`) | Complete |
| Configuration files (`.env.example`, `.gitignore`, `pyproject.toml`, `README.md`) | Complete |
| SQLAlchemy 2.0 database engine configuration | Complete (`back/src/core/database.py`) |
| SQLAlchemy session factory (`SessionLocal`) | Complete (`back/src/core/database.py`, commit `3ea0199`) |
| SQLAlchemy session dependency (`get_db()`) | Complete (`back/src/core/database.py`, commit `667a965`) |
| Alembic migration environment | Complete (`back/alembic.ini`, commit `5d17e69`; `back/alembic/env.py`, commit `23d10dc`) |
| Database models (users, sellers, stores, categories, products) | Complete (`back/src/core/models/`, commits `0f058ac`, `98436eb`, `50e5169`, `ff424f2`) |
| Model unit tests | Complete (`back/tests/test_models_unit.py`, commit `935200d`) |
| Psycopg 3 driver dependency | Complete (`back/pyproject.toml`, commit `d055846`) |
| Local PostgreSQL instance | Not yet provisioned |

## Prerequisites (must be in place before implementation)

- Local PostgreSQL installed and running
- Development database created (`plataforma_comercio_dev`)
- `DATABASE_URL` configured in `back/.env`
- RLS policies designed (per `SECURITY.md` row-level security requirement)

## Completion Criteria

- [ ] `alembic revision --autogenerate -m "initial migration"` creates migration file
- [ ] Migration file contains `users`, `sellers`, `stores`, `categories`, `products` tables
- [ ] `alembic upgrade head` applies migration successfully against PostgreSQL
- [ ] `alembic current` shows the applied migration

## Authorization Required

**The user must explicitly approve this implementation task before work begins.** No code will be written until authorization is given.

## Subsequent Units (after Alembic migration)

1. **Authentication module** (auth-module): User registration, login, JWT, Argon2, login/register endpoints
2. **Basic tests**: Authentication and database connection tests
