# NEXT_STEPS.md

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

## Next Recommended Implementation Unit

**Cart module remaining endpoints** (cart-module): POST /{cart_id}/validate, POST /{cart_id}/merge/{guest_cart_id}

This unit builds on the completed authentication module, seller module, product module, category module, and complete cart module.

## Current Development Phase

**Phase 1: Fundamentals** (Weeks 1-2)

**Backend infrastructure — Complete**

| Dependency | Status |
|------------|--------|
| Backend directory structure (`back/src/`, `back/tests/`, `back/alembic/`) | Complete |
| Configuration files (`.env.example`, `.gitignore`, `pyproject.toml`, `README.md`) | Complete |
| Pytest Python import path (`pythonpath` in `pyproject.toml`) | Complete (commit `14470c9`) |
| FastAPI application entry point (`back/src/main.py`) | Complete (commit `79367fd`) |
| SQLAlchemy 2.0 database engine + session factory + `get_db()` dependency | Complete |
| Alembic migration environment + initial migration applied | Complete (revision `31b998880986` on `plataforma_comercio_dev`) |
| Revoked refresh token migration applied | Complete (revision `b67c867d7c26` on `plataforma_comercio_dev`) |
| Database models (users, sellers, stores, categories, products, revoked_refresh_tokens, carts, cart_items) | Complete |
| Cart and CartItem Alembic migration (revision `7f3a1e2c4d8b`) | Applied to `plataforma_comercio_dev` (commit `b586e55`) |
| Alembic migration directory tracking (`.gitignore` allows `*.py` files) | Complete (commit `ba13a24`) |
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
| Product module — full CRUD + listing | Complete (commits `473585d`, `4e70d90`, `3a93791`, `e3f2273`, `6dc8a3a`) |
| Category module — full CRUD + listing | Complete (commit `b7f0f02`) |
| Category module — admin authorization | Complete (commit `c8e3762`) |
| Cart module — full CRUD + item management | Complete (commits `e9efb6d`, `37ea458`, `d16c02d`, `b64329a`) |
| Cart service/repository refactoring — all persistence moved to repositories | Complete (commits `dc57c2a`, `b2128e7`, `0d1b6cb`, `488bcea`) |
| Test reorganization — modular test directory structure | Complete (commits `3b0a669`, `3a941be`, `a4ef954`, `74a5774`, `5409d4f`, `5b45d3d`, `5c3ab0d`) |
| Database engine compatibility fix — `create_db_engine()` SQLite/PostgreSQL support | Complete (commit `5c62cf0`) |
| Alembic and settings test corrections — A1–A6 in test_alembic_unit.py | Complete (commit `8e20eff`) |
| Model test corrections — C1–C11 in test_models_unit.py | Complete (commit `f20d2e6`) |
| Model default flush verification — C1–C11 post-flush tests | Complete (commit `dd9a580`) |
| Session test corrections — D1–D4 in test_session_unit.py | Complete (commit `204b9b0`) |
| Database engine configuration test corrections — B1, B4–B7 in test_database_unit.py | Complete (commit `f222067`) |
| Orders Unit 1: Database Migration + SQLAlchemy Models | Complete (commits `a0a3c81`, `495f520`, `a2a43c6`) |
| Local PostgreSQL instance | Provisioned |
| Development database (`plataforma_comercio_dev`) | Created and migrated |
| `DATABASE_URL` configured in `back/.env` | Configured |

## Orders Unit 1 — Completed

| Item | Status |
|------|--------|
| Order, OrderItem, OrderSubitem, Payment, Commission models | Complete (commit `a0a3c81`) |
| Product.reserved_quantity field + CHECK constraints | Complete (commit `a0a3c81`) |
| Alembic migration revision `8e7f6d5c4b3a` | Complete (commit `495f520`) |
| Order model unit tests (70 tests) | Complete (commit `a2a43c6`) |
| Full regression suite | 398 passed, 0 failed, 9 skipped |
| Migration applied to database | Not yet applied (pending user authorization) |

## Next Recommended Implementation Unit

**Orders Unit 2: Order Services and Repository**

Create order service layer (`back/src/core/orders/services.py`) and order repository layer (`back/src/core/orders/repositories.py`) following the cart module pattern:
- Order creation from cart items
- Order retrieval
- Order status transitions
- Seller sub-order grouping
- Cart validation before order creation
