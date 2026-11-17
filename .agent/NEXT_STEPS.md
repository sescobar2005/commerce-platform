# NEXT_STEPS.md

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Next Recommended Implementation Unit

**Authentication module endpoints - Logout** — User logout (`POST /api/v1/auth/logout`).

This unit builds on the completed password security service (Argon2id), JWT token service (RS256), authentication Pydantic schemas, registration endpoint, login endpoint, and authentication dependencies (get_current_user).

## Dependencies

| Dependency | Status |
|------------|--------|
| Backend directory structure (`back/src/`, `back/tests/`, `back/alembic/`) | Complete |
| Configuration files (`.env.example`, `.gitignore`, `pyproject.toml`, `README.md`) | Complete |
| SQLAlchemy 2.0 database engine + session factory + `get_db()` dependency | Complete |
| Alembic migration environment + initial migration applied | Complete (revision `31b998880986` on `plataforma_comercio_dev`) |
| Database models (users, sellers, stores, categories, products) | Complete |
| Password security service (Argon2id) + unit tests | Complete |
| JWT token service (RS256) + unit tests | Complete |
| Authentication Pydantic schemas + unit tests | Complete |
| Registration endpoint + unit tests | Complete |
| Login endpoint + unit tests | Complete |
| Authentication dependencies (get_current_user) + unit tests | Complete |
| Psycopg 3 driver dependency | Complete |
| Local PostgreSQL instance | Provisioned |
| Development database (`plataforma_comercio_dev`) | Created and migrated |
| `DATABASE_URL` configured in `back/.env` | Configured |

## Prerequisites (must be in place before implementation)

- All database infrastructure complete and verified
- Password security service complete and tested
- JWT token service complete and tested
- Authentication schemas complete and tested
- Registration endpoint complete and tested
- Login endpoint complete and tested
- Authentication dependencies complete and tested
- JWT RSA key files configured at paths specified in `JWT_PRIVATE_KEY_PATH` and `JWT_PUBLIC_KEY_PATH`

## Completion Criteria

- [ ] User logout endpoint (`POST /api/v1/auth/logout`)
- [ ] Authentication unit and integration tests for logout

## Authorization Required

**The user must explicitly approve this implementation task before work begins.** No code will be written until authorization is given.

## Subsequent Units

1. **Seller module** (seller-module): Seller registration, store management
2. **Product module** (product-module): Product catalog, inventory
3. **Cart module** (cart-module): Shopping cart functionality
4. **Order module** (order-module): Orders, sub-orders, payments
