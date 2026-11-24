# CURRENT_TASK.md

## Current Task Information

| Field | Value |
|-------|-------|
| Current phase | 1 (Fundamentals) → Phase 2 (Database Stabilization) |
| Current task | Cart and CartItem database models + migration |
| Objective | Implement Cart and CartItem SQLAlchemy 2.0 database models with relationships and constraints, create Alembic migration, fix .gitignore for migration tracking |
| Scope | `back/src/core/models/cart.py`, `back/src/core/models/__init__.py`, `back/alembic/env.py`, `back/alembic/versions/7f3a1e2c4d8b_add_cart_and_cart_item_tables.py`, `back/.gitignore`, `back/tests/test_cart_models_unit.py` |
| Files involved | `back/src/main.py`, `back/src/core/cart/__init__.py`, `back/src/core/cart/schemas.py`, `back/src/core/cart/router.py`, `back/src/core/models/cart.py`, `back/src/core/models/__init__.py`, `back/alembic/env.py`, `back/alembic/versions/7f3a1e2c4d8b_add_cart_and_cart_item_tables.py`, `back/.gitignore`, `back/tests/test_cart_models_unit.py`, `back/tests/test_cart_unit.py`, `back/tests/test_cart_item_unit.py`, `back/tests/test_cart_update_delete_unit.py` |
| Completed units | All auth endpoints, all product endpoints, all category endpoints, all cart endpoints (create, retrieve, update, delete, add item, update item, remove item), Cart models (Cart, CartItem), Cart migrations, FastAPI entry point, Config fix (ALGORITHM optional), Alembic .gitignore fix, Cart/CartItem migration |
| Pending units | Cart module remaining endpoints (validate, merge), Order module |
| Verification status | 225/225 tests pass; App imports and starts successfully; 25 API routes registered; Alembic migration chain: base → 31b998880986 → b67c867d7c26 → 7f3a1e2c4d8b (head); `alembic upgrade head --sql` generates valid SQL; Python syntax verified for all files |
| Last updated | 2026-11-24 |

### Notes

Cart service/repository refactoring (commits `dc57c2a`, `b2128e7`, `0d1b6cb`, `488bcea`):
- All persistence operations (db.add()/db.delete()/db.commit()/db.rollback()/db.refresh()) moved from CartService to CartRepository/CartItemRepository
- CartRepository: add, delete, get_by_id, get_by_user_id, commit, rollback, refresh
- CartItemRepository: add, delete, get_by_id, get_by_cart_and_product, commit, rollback, refresh
- Decision: No ProductRepository created — only 2 read-only Product queries remain in CartService; no existing ProductRepository pattern in codebase; creating one would be unnecessary abstraction
- All 64 cart unit tests pass (64 passed, 0 failed, 0 skipped)

### Notes

Configuration fix (commit `c6752fd`):
- Removed `ALGORITHM` as required field; changed to optional with default `RS256`
- `JWT_ALGORITHM` is the field actually used by JWTService

Authentication module (commits `6a52190`, `1edbb42`, `1edbb42`, `25afd42`, `0ac4f11`):
- POST /api/v1/auth/register, POST /api/v1/auth/login, POST /api/v1/auth/refresh, POST /api/v1/auth/logout
- Authentication dependencies (get_current_user)
- JWTService with RS256, Argon2id password hashing, TokenRevocationService
- UserResponse (public) excludes is_admin; CurrentUser (internal) includes is_admin

Seller module (commits `5b86ca2`):
- POST /api/v1/sellers/register, POST /api/v1/sellers/{seller_id}/stores, GET /api/v1/sellers/{seller_id}

Product module (commits `473585d`, `4e70d90`, `3a93791`, `e3f2273`, `6dc8a3a`):
- Full CRUD + listing endpoints

Category module (commits `b7f0f02`, `c8e3762`):
- Full CRUD + listing + product listing + admin authorization

Cart module (commits `e9efb6d`, `37ea458`, `d16c02d`, `b64329a`):
- Full CRUD + item management endpoints

Database infrastructure (commits `79367fd`, `c6752fd`, `ba13a24`, `b586e55`, `19d1120`):
- back/src/main.py - FastAPI app entry point with all 5 routers registered
- config.py - ALGORITHM made optional with RS256 default
- .gitignore - alembic/versions/* now tracked (except *.py files)
- cart.py - Cart and CartItem SQLAlchemy models
- 7f3a1e2c4d8b - Cart and CartItem Alembic migration APPLIED to plataforma_comercio_dev
- Verified: Alembic revision is `7f3a1e2c4d8b`, carts and cart_items tables exist with all columns/constraints/indexes, all 7 original tables preserved intact

All pre-existing test failures (28) are unrelated SQLAlchemy model default / Alembic / session issues.

### Expiration analysis (2026-11-24)

| Field | Value |
|-------|-------|
| expires_at nullable? | Yes — model: `Optional[datetime]`, `nullable=True`; schema: `Optional[datetime] = Field(None)`; test `test_cart_update_clear_expiration` asserts `expires_at is None` |
| Future-date validation documented? | No — API_SPECIFICATION.md, model (no check constraint), schema (no Pydantic validation), service (no validation) all lack future-date rule |
| Timezone consistency | Inconsistent — model uses `DateTime(timezone=True)`, but tests and schema use naive datetimes (e.g., `datetime(2024, 12, 31)`) |
| Decision | Do NOT implement future-date validation — requirements do not support it. No production code, test, or exception changes made. |