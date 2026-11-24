# NEXT_STEPS.md

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Next Recommended Implementation Unit

**Cart module** (cart-module): Shopping cart functionality.

This unit builds on the completed authentication module, seller module, product module, and category module.

## Dependencies

| Dependency | Status |
|------------|--------|
| Backend directory structure (`back/src/`, `back/tests/`, `back/alembic/`) | Complete |
| Configuration files (`.env.example`, `.gitignore`, `pyproject.toml`, `README.md`) | Complete |
| Pytest Python import path (`pythonpath` in `pyproject.toml`) | Complete (commit `14470c9`) |
| SQLAlchemy 2.0 database engine + session factory + `get_db()` dependency | Complete |
| Alembic migration environment + initial migration applied | Complete (revision `31b998880986` on `plataforma_comercio_dev`) |
| Revoked refresh token migration applied | Complete (revision `b67c867d7c26` on `plataforma_comercio_dev`) |
| Database models (users, sellers, stores, categories, products, revoked_refresh_tokens, carts, cart_items) | Complete |
| Password security service (Argon2id) + unit tests | Complete |
| JWT token service (RS256) + unit tests | Complete |
| Authentication Pydantic schemas + unit tests | Complete |
| UserResponse (public) excludes is_admin; CurrentUser (internal) includes is_admin | Complete |
| Registration endpoint + unit tests | Complete |
| Login endpoint + unit tests | Complete |
| Refresh token endpoint + unit tests | Complete (commit `25afd42`) |
| Logout endpoint + unit tests | Complete |
| Authentication dependencies (get_current_user) + unit tests | Complete |
| Token revocation service + unit tests | Complete |
| Product module — creation endpoint (`POST /api/v1/products`) | Complete (commit `473585d`) |
| Product module — retrieval endpoint (`GET /api/v1/products/{product_id}`) | Complete (commit `4e70d90`) |
| Product module — update endpoint (`PUT /api/v1/products/{product_id}`) | Complete (commit `3a93791`) |
| Product module — deletion endpoint (`DELETE /api/v1/products/{product_id}`) | Complete (commit `e3f2273`) |
| Product module — deletion unit tests (6/6 unit tests pass) | Complete |
| Product module — listing endpoint (`GET /api/v1/products/`) | Complete (commit `6dc8a3a`) |
| Product module — listing unit tests (17/17 unit tests pass) | Complete |
| Category module — full CRUD and listing | Complete (commit `b7f0f02`) |
| Category module — admin authorization for write endpoints | Complete (commit `c8e3762`) |
| Category module — unit tests (37/37 unit tests pass) | Complete |
| Psycopg 3 driver dependency | Complete |
| Local PostgreSQL instance | Provisioned |
| Development database (`plataforma_comercio_dev`) | Created and migrated |
| `DATABASE_URL` configured in `back/.env` | Configured |

## Prerequisites (must be in place before implementation)

- All database infrastructure complete and verified
- All authentication modules complete and tested
- JWT RSA key files configured at paths specified in `JWT_PRIVATE_KEY_PATH` and `JWT_PUBLIC_KEY_PATH`

## Completion Criteria

- [x] Seller registration endpoint (`POST /api/v1/sellers/register`)
- [x] Seller store creation endpoint (`POST /api/v1/sellers/{seller_id}/stores`)
- [x] Seller profile retrieval endpoint (`GET /api/v1/sellers/{seller_id}`)
- [x] Seller unit and integration tests (10/10 unit tests pass)
- [x] Product creation endpoint (`POST /api/v1/products`)
- [x] Product unit tests (8/8 unit tests pass)
- [x] Product retrieval endpoint (`GET /api/v1/products/{product_id}`)
- [x] Product retrieval unit tests (3/3 unit tests pass)
- [x] Product update endpoint (`PUT /api/v1/products/{product_id}`)
- [x] Product update unit tests (8/8 unit tests pass)
- [x] Product deletion endpoint (`DELETE /api/v1/products/{product_id}`)
- [x] Product deletion unit tests (6/6 unit tests pass)
- [x] Product listing endpoint (`GET /api/v1/products/`)
- [x] Product listing unit tests (17/17 unit tests pass)
- [x] Category creation endpoint (`POST /api/v1/categories/`)
- [x] Category retrieval endpoint (`GET /api/v1/categories/{category_id}`)
- [x] Category update endpoint (`PUT /api/v1/categories/{category_id}`)
- [x] Category deletion endpoint (`DELETE /api/v1/categories/{category_id}`)
- [x] Category listing endpoint (`GET /api/v1/categories/`)
- [x] Category product listing endpoint (`GET /api/v1/categories/{category_id}/products`)
- [x] Category admin authorization (POST/PUT/DELETE require is_admin, GET public)
- [x] Category unit tests (37/37 unit tests pass)
- [x] Cart module — Cart and CartItem models (commit `e9efb6d`)
- [x] Cart module — model unit tests (20/20 unit tests pass)
- [x] Cart creation endpoint (`POST /api/v1/carts/`) — commit `37ea458`
- [x] Cart retrieval endpoint (`GET /api/v1/carts/{cart_id}`) — commit `37ea458`
- [x] Cart update endpoint (`PUT /api/v1/carts/{cart_id}`) — commit `b64329a`
- [x] Cart delete endpoint (`DELETE /api/v1/carts/{cart_id}`) — commit `b64329a`
- [x] Cart update/delete unit tests (12/12 unit tests pass)
- [x] Cart item add endpoint (`POST /api/v1/carts/{cart_id}/items`) — commit `d16c02d`
- [x] Cart item update endpoint (`PUT /api/v1/carts/{cart_id}/items/{item_id}`) — commit `d16c02d`
- [x] Cart item remove endpoint (`DELETE /api/v1/carts/{cart_id}/items/{item_id}`) — commit `d16c02d`
- [x] Cart item unit tests (21/21 unit tests pass)

## Authorization Required

**The user must explicitly approve this implementation task before work begins.** No code will be written until authorization is given.

## Subsequent Units

1. **Cart module remaining endpoints** (cart-module): POST /{cart_id}/validate, POST /{cart_id}/merge/{guest_cart_id}
2. **Order module** (order-module): Orders, sub-orders, payments
