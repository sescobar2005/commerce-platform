# NEXT_STEPS.md

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Next Recommended Implementation Unit

**Refresh token endpoint** (`POST /api/v1/auth/refresh`).

This unit builds on the completed password security service (Argon2id), JWT token service (RS256), authentication Pydantic schemas, registration endpoint, login endpoint, authentication dependencies (get_current_user), and refresh token revocation foundation.

## Dependencies

| Dependency | Status |
|------------|--------|
| Backend directory structure (`back/src/`, `back/tests/`, `back/alembic/`) | Complete |
| Configuration files (`.env.example`, `.gitignore`, `pyproject.toml`, `README.md`) | Complete |
| SQLAlchemy 2.0 database engine + session factory + `get_db()` dependency | Complete |
| Alembic migration environment + initial migration applied | Complete (revision `31b998880986` on `plataforma_comercio_dev`) |
| Revoked refresh token migration applied | Pending (revision `b67c867d7c26`) |
| Database models (users, sellers, stores, categories, products, revoked_refresh_tokens) | Complete |
| Password security service (Argon2id) + unit tests | Complete |
| JWT token service (RS256) + unit tests | Complete |
| Authentication Pydantic schemas + unit tests | Complete |
| Registration endpoint + unit tests | Complete |
| Login endpoint + unit tests | Complete |
| Authentication dependencies (get_current_user) + unit tests | Complete |
| Token revocation service + unit tests | Complete |
| Psycopg 3 driver dependency | Complete |
| Local PostgreSQL instance | Provisioned |
| Development database (`plataforma_comercio_dev`) | Created and migrated (without revoked_refresh_tokens migration applied yet) |
| `DATABASE_URL` configured in `back/.env` | Configured |

## Prerequisites (must be in place before implementation)

- All database infrastructure complete and verified
- Apply Alembic migration `b67c867d7c26` to `plataforma_comercio_dev` for revoked_refresh_tokens table
- Password security service complete and tested
- JWT token service complete and tested
- Authentication schemas complete and tested
- Registration endpoint complete and tested
- Login endpoint complete and tested
- Authentication dependencies complete and tested
- Token revocation service complete and tested
- JWT RSA key files configured at paths specified in `JWT_PRIVATE_KEY_PATH` and `JWT_PUBLIC_KEY_PATH`

## Completion Criteria

- [ ] Refresh token endpoint (`POST /api/v1/auth/refresh`)
- [ ] Revocation check before issuing new access token
- [ ] Reject revoked refresh tokens
- [ ] Token rotation (optional, decision pending)
- [ ] Authentication unit and integration tests for refresh endpoint

## Authorization Required

**The user must explicitly approve this implementation task before work begins.** No code will be written until authorization is given.

## Subsequent Units

1. **Logout endpoint** (`POST /api/v1/auth/logout`) - Revoke refresh token
2. **Seller module** (seller-module): Seller registration, store management
3. **Product module** (product-module): Product catalog, inventory
4. **Cart module** (cart-module): Shopping cart functionality
5. **Order module** (order-module): Orders, sub-orders, payments
