# CURRENT_TASK.md

## Current Task Information

| Field | Value |
|-------|-------|
| Current phase | 1 (Fundamentals) |
| Current task | Cart module — cart update and delete endpoints |
| Objective | Implement PUT /api/v1/carts/{cart_id} and DELETE /api/v1/carts/{cart_id} |
| Scope | `back/src/core/cart/schemas.py`, `back/src/core/cart/router.py`, `back/tests/test_cart_update_delete_unit.py` |
| Files involved | `back/src/core/cart/__init__.py`, `back/src/core/cart/schemas.py`, `back/src/core/cart/router.py`, `back/tests/test_cart_update_delete_unit.py`, `back/tests/test_cart_unit.py` |
| Completed units | Documentation baseline (6 docs), backend directory structure, config files, database engine configuration + connection pooling, unit tests, integration tests, SQLAlchemy session factory, session lifecycle/FastAPI dependency, Alembic configuration + initial migration applied to plataforma_comercio_dev, database models (users, sellers, stores, categories, products, revoked_refresh_tokens, carts, cart_items), Password service (Argon2id), JWT service (RS256), Authentication schemas, Registration endpoint, Login endpoint, Authentication dependencies, Refresh token endpoint, Logout endpoint, Seller module (registration, store creation, profile retrieval), Product module (create, retrieve, update, delete, list), Category module (create, retrieve, update, delete, list, list products) with admin authorization, Cart models (Cart, CartItem), Cart creation endpoint, Cart retrieval endpoint, Cart item add/update/remove endpoints, Cart update endpoint, Cart delete endpoint |
| Pending units | Cart module endpoints: POST /{cart_id}/validate, POST /{cart_id}/merge/{guest_cart_id}), Order module |
| Verification status | 12/12 cart update/delete unit tests pass; 21/21 cart item tests pass; 11/11 cart endpoint tests pass; 20/20 cart model tests pass; 42/42 product unit tests pass; 37/37 category unit tests pass; 9/9 refresh unit tests pass; 72/72 auth tests pass; 10/10 seller tests pass; 225/225 regression tests pass; Python syntax verified for all files |
| Last updated | 2026-11-23 |

### Notes

Cart module complete CRUD:
- POST /api/v1/carts/ — Create cart (commit `37ea458`)
- GET /api/v1/carts/{cart_id} — Retrieve cart (commit `37ea458`)
- PUT /api/v1/carts/{cart_id} — Update expires_at only (commit `b64329a`)
- DELETE /api/v1/carts/{cart_id} — Delete cart with cascade (commit `b64329a`)
- POST /api/v1/carts/{cart_id}/items — Add item (commit `d16c02d`)
- PUT /api/v1/carts/{cart_id}/items/{item_id} — Update item quantity (commit `d16c02d`)
- DELETE /api/v1/carts/{cart_id}/items/{item_id} — Remove item (commit `d16c02d`)

PUT /{cart_id}: Updates only expires_at. Ownership, created_at, last_updated_at not editable.
DELETE /{cart_id}: Deletes cart with cascade delete-orphan on items.
All endpoints require authentication; cart ownership verified; 404 for non-owner (information disclosure prevention).
IntegrityError → 409 with rollback.

All pre-existing test failures (28) are unrelated SQLAlchemy 2.0 model default / Alembic / session issues.
