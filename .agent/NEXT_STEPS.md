# NEXT_STEPS.md

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Next Recommended Implementation Unit

**JWT token management** — Implement JWT token generation and validation using RS256 algorithm per SECURITY.md.

This unit builds on the completed password security service. JWT tokens will be used for authentication in the authentication module endpoints.

## Dependencies

| Dependency | Status |
|------------|--------|
| Backend directory structure (`back/src/`, `back/tests/`, `back/alembic/`) | Complete |
| Configuration files (`.env.example`, `.gitignore`, `pyproject.toml`, `README.md`) | Complete |
| SQLAlchemy 2.0 database engine + session factory + `get_db()` dependency | Complete |
| Alembic migration environment + initial migration applied | Complete (revision `31b998880986` on `plataforma_comercio_dev`) |
| Database models (users, sellers, stores, categories, products) | Complete |
| Database models (users, sellers, stores, categories, products) | Complete |
| Password security service (Argon2id) + unit tests | Complete (`back/src/core/security/password.py`) |
| Psycopg 3 driver dependency | Complete |
| Local PostgreSQL instance | Provisioned |
| Development database (`plataforma_comercio_dev`) | Created and migrated |
| `DATABASE_URL` configured in `back/.env` | Configured |

## Prerequisites (must be in place before implementation)

- All database infrastructure complete and verified
- Password security service complete and tested
- JWT secret key configured in `.env`
- python-jose[cryptography] library available (already in pyproject.toml)

## Completion Criteria

- [ ] JWT token generation with RS256 algorithm
- [ ] JWT token validation and expiration checking
- [ ] Token payload includes user_id, username, role, exp, iat
- [ ] Unit tests for JWT generation and validation
- [ ] No plaintext secrets in logs or code

## Authorization Required

**The user must explicitly approve this implementation task before work begins.** No code will be written until authorization is given.

## Subsequent Units

1. **Authentication module endpoints** — User registration (`POST /api/v1/auth/register`), login (`POST /api/v1/auth/login`), logout (`POST /api/v1/auth/logout`)
2. **Seller module** (seller-module): Seller registration, store management
3. **Product module** (product-module): Product catalog, inventory
4. **Cart module** (cart-module): Shopping cart functionality
5. **Order module** (order-module): Orders, sub-orders, payments
