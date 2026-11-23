# NEXT_STEPS.md

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Next Recommended Implementation Unit

**Seller module** (seller-module): Seller registration, store management.

This unit builds on the completed authentication module (registration, login, logout, JWT, password security, refresh token revocation).

## Dependencies

| Dependency | Status |
|------------|--------|
| Backend directory structure (`back/src/`, `back/tests/`, `back/alembic/`) | Complete |
| Configuration files (`.env.example`, `.gitignore`, `pyproject.toml`, `README.md`) | Complete |
| SQLAlchemy 2.0 database engine + session factory + `get_db()` dependency | Complete |
| Alembic migration environment + initial migration applied | Complete (revision `31b998880986` on `plataforma_comercio_dev`) |
| Revoked refresh token migration applied | Complete (revision `b67c867d7c26` on `plataforma_comercio_dev`) |
| Database models (users, sellers, stores, categories, products, revoked_refresh_tokens) | Complete |
| Password security service (Argon2id) + unit tests | Complete |
| JWT token service (RS256) + unit tests | Complete |
| Authentication Pydantic schemas + unit tests | Complete |
| Registration endpoint + unit tests | Complete |
| Login endpoint + unit tests | Complete |
| Logout endpoint + unit tests | Complete |
| Authentication dependencies (get_current_user) + unit tests | Complete |
| Token revocation service + unit tests | Complete |
| Psycopg 3 driver dependency | Complete |
| Local PostgreSQL instance | Provisioned |
| Development database (`plataforma_comercio_dev`) | Created and migrated |
| `DATABASE_URL` configured in `back/.env` | Configured |

## Prerequisites (must be in place before implementation)

- All database infrastructure complete and verified
- All authentication modules complete and tested
- JWT RSA key files configured at paths specified in `JWT_PRIVATE_KEY_PATH` and `JWT_PUBLIC_KEY_PATH`

## Completion Criteria

- [ ] Seller registration endpoint (`POST /api/v1/sellers/register`)
- [ ] Seller store creation endpoint (`POST /api/v1/sellers/{seller_id}/stores`)
- [ ] Seller profile retrieval endpoint (`GET /api/v1/sellers/{seller_id}`)
- [ ] Seller unit and integration tests

## Authorization Required

**The user must explicitly approve this implementation task before work begins.** No code will be written until authorization is given.

## Subsequent Units

1. **Product module** (product-module): Product catalog, inventory
2. **Cart module** (cart-module): Shopping cart functionality
3. **Order module** (order-module): Orders, sub-orders, payments
