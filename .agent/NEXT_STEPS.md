# NEXT_STEPS.md

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Next Recommended Implementation Unit

**Authentication module** (auth-module): User registration, login, JWT token management, Argon2 password hashing, login/register endpoints.

This unit builds on the completed database foundation (engine, sessions, models, migration applied to `plataforma_comercio_dev`).

## Dependencies

| Dependency | Status |
|------------|--------|
| Backend directory structure (`back/src/`, `back/tests/`, `back/alembic/`) | Complete |
| Configuration files (`.env.example`, `.gitignore`, `pyproject.toml`, `README.md`) | Complete |
| SQLAlchemy 2.0 database engine + session factory + `get_db()` dependency | Complete |
| Alembic migration environment + initial migration applied | Complete (revision `31b998880986` on `plataforma_comercio_dev`) |
| Database models (users, sellers, stores, categories, products) | Complete |
| Psycopg 3 driver dependency | Complete |
| Local PostgreSQL instance | Provisioned |
| Development database (`plataforma_comercio_dev`) | Created and migrated |
| `DATABASE_URL` configured in `back/.env` | Configured |

## Prerequisites (must be in place before implementation)

- All database infrastructure complete and verified
- JWT secret key configured in `.env`
- Argon2 password hashing library available

## Completion Criteria

- [ ] User registration endpoint (`POST /api/v1/auth/register`)
- [ ] User login endpoint (`POST /api/v1/auth/login`)
- [ ] JWT token generation and validation
- [ ] Argon2 password hashing
- [ ] Password reset flow
- [ ] Authentication unit and integration tests

## Authorization Required

**The user must explicitly approve this implementation task before work begins.** No code will be written until authorization is given.

## Subsequent Units

1. **Seller module** (seller-module): Seller registration, store management
2. **Product module** (product-module): Product catalog, inventory
3. **Cart module** (cart-module): Shopping cart functionality
4. **Order module** (order-module): Orders, sub-orders, payments
