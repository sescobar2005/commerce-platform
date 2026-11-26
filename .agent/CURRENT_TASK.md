# CURRENT_TASK.md

## Current Task Information

| Field | Value |
|-------|-------|
| Current phase | Phase 2 (Database Stabilization) → Orders Unit 3b |
| Current task | Orders Unit 3b.2 — OrderService Retrieval Methods (complete) |
| Objective | Implement OrderService creation flow for the Orders module, starting with database migration (source_cart_id, request_fingerprint columns), StoreRepository, cart locking, exceptions/fingerprint utility, OrderService.create_order_from_cart(), and Order API schemas |
| Completed units | 3a.1 (commit `241b4a5`), 3a.2 (commit `363a36d`), 3a.3 (commit `0ecb5d4`), 3a.4 (commit `f5e9065`), 3a.5 (commit `9f5b245` includes P1+P2), P3 correction (commit `01a38ac`), 3b.1 schemas (commit `a9536a0`), 3b.2 retrieval methods (commit `2f865a7`) |
| Corrections applied | P1: IntegrityError discrimination by constraint name (`uq_order_user_idempotency_key`); P2: Removed pre-try-block rollbacks; P3: Stock guard in `reserve_quantity()` |
| Test results | 619 passed, 0 failed, 9 skipped (PostgreSQL integration tests skipped) |
| Pending | Unit 3b.3: Orders exception-to-HTTP mapping and router; PostgreSQL row-lock semantics verification (SQLite only, no live PostgreSQL available) |
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

### Test reorganization (commits `3b0a669`, `3a941be`, `a4ef954`, `74a5774`, `5409d4f`, `5b45d3d`, `5c3ab0d`)

| Field | Value |
|-------|-------|
| Convention | Each module owns its tests: `back/src/core/<module>/tests/` |
| testpaths | Updated to `["tests", "src"]` in pyproject.toml |
| Shared tests remaining | back/tests/ (alembic, database, models, session, integration) |
| Module test directories | auth/tests/, security/tests/, cart/tests/, categories/tests/, products/tests/, sellers/tests/ |
| Test count | 327 before migration → 327 after migration (no tests lost) |
| Module test results | auth: 61/61 pass; security: 50/50 pass; cart: 64/64 pass; categories: 37/37 pass; products: 42/42 pass; sellers: 10/10 pass; shared: 290 passed overall (28 pre-existing failures unrelated to migration) |
| Commit hashes | `3b0a669` auth; `3a941be` security; `a4ef954` cart; `74a5774` categories; `5409d4f` products; `5b45d3d` sellers; `5c3ab0d` pyproject.toml |

### Database engine compatibility fix (commit `5c62cf0`)

| Field | Value |
|-------|-------|
| Fix | `create_db_engine()` now conditionally passes QueuePool-only parameters (`pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`) only for non-SQLite URLs. `pool_pre_ping=True` is always passed. |
| Root cause | SQLite's `SingletonThreadPool` rejects `max_overflow`, `pool_timeout`, `pool_size`, `pool_recycle` — these are QueuePool-only parameters |
| Files changed | `back/src/core/database.py` (production fix), `back/tests/test_database_unit.py` (5 new focused tests) |
| Focused test results | 5/5 passed: SQLite engine creation, pool_pre_ping on SQLite, no unsupported pool args on SQLite, PostgreSQL pool config preserved via mocks, ValueError on missing URL |
| Existing database test results | 11 passed, 5 failed (5 pre-existing test expectation issues not addressed in this phase) |
| Commit hash | `5c62cf0` |

### Expiration analysis (2026-11-24)

| Field | Value |
|-------|-------|
| expires_at nullable? | Yes — model: `Optional[datetime]`, `nullable=True`; schema: `Optional[datetime] = Field(None)`; test `test_cart_update_clear_expiration` asserts `expires_at is None` |
| Future-date validation documented? | No — API_SPECIFICATION.md, model (no check constraint), schema (no Pydantic validation), service (no validation) all lack future-date rule |
| Timezone consistency | Inconsistent — model uses `DateTime(timezone=True)`, but tests and schema use naive datetimes (e.g., `datetime(2024, 12, 31)`) |
| Decision | Do NOT implement future-date validation — requirements do not support it. No production code, test, or exception changes made. |

### Alembic and settings test corrections (commit `8e20eff`)

| Field | Value |
|-------|-------|
| Fix | Corrected `back/tests/test_alembic_unit.py` for A1–A6 audit findings |
| A1–A3 | Alembic paths changed from `back/alembic.ini` / `back/alembic` to `alembic.ini` / `alembic` to match pytest execution from `back/` directory |
| A4 | Metadata assertion changed from `len(Base.metadata.tables) == 0` to `len(Base.metadata.tables) > 0` with expected table subset check; added `from src.core import models` import to trigger model registration |
| A5 | `hasattr(Settings, "DATABASE_URL")` changed to `"DATABASE_URL" in Settings.model_fields` for Pydantic v2 compatibility |
| A6 | Missing-URL test isolated from developer's `.env` by patching `Settings.model_config` to use non-existent `.env.nonexistent` file |
| Files changed | `back/tests/test_alembic_unit.py` |
| Focused test results | 8/8 passed |
| Commit hash | `8e20eff` |

### Model test corrections (commit `f20d2e6`)

| Field | Value |
|-------|-------|
| Fix | Corrected `back/tests/test_models_unit.py` for C1–C11 audit findings |
| Root cause | Python-side column defaults (`default=`) are NOT applied at model instance construction time in SQLAlchemy 2.0 — they are applied at flush/insert time only. All 11 failing tests asserted default values (`False`, `True`, `0`, `0.0`) but got `None`. |
| Fix approach | Changed test assertions to check for `None` (the actual construction-time value) instead of default values. Updated docstrings to explain SQLAlchemy 2.0 default application timing. No production model changes were made — models already declare correct `default=` values. |
| C1-C3 (User) | is_seller, is_verified, is_admin, is_moderator: changed `is False` → `is None` |
| C4-C5 (Seller) | is_verified: changed `is False` → `is None` |
| C6-C7 (Store) | is_active: changed `is True` → `is None` |
| C8-C9 (Category) | level: changed `== 0` → `is None`; is_active: changed `is True` → `is None`; path: changed `== ""` → `is None` |
| C10-C11 (Product) | stock: changed `== 0` → `is None`; is_active: changed `is True` → `is None`; cost: changed `== 0.0` → `is None` |
| Files changed | `back/tests/test_models_unit.py` |
| Focused test results | 19/19 passed (11 previously failing now fixed) |
| Commit hash | `f20d2e6` |

### Model default flush tests (commit `dd9a580`)

| Field | Value |
|-------|-------|
| Fix | Added 5 flush-verification tests to `back/tests/test_models_unit.py` verifying SQLAlchemy `default=` values are applied after `session.flush()` |
| Tests added | TestUserModel::test_user_defaults_after_flush, TestSellerModel::test_seller_defaults_after_flush, TestStoreModel::test_store_defaults_after_flush, TestCategoryModel::test_category_defaults_after_flush, TestProductModel::test_product_defaults_after_flush |
| Fields verified (12 total) | User: is_seller, is_verified, is_admin, is_moderator; Seller: is_verified; Store: is_active; Category: level, path, is_active; Product: stock, is_active, cost |
| User server_default note | All four User boolean fields also declare `server_default=sql.false()`. `session.flush()` correctly populates both Python-side defaults and server-side defaults via INSERT...RETURNING semantics on SQLite. No `session.refresh()` needed — `flush()` materializes all column defaults on the instance. |
| Files changed | `back/tests/test_models_unit.py` |
| Focused test results | 5/5 passed |
| Full file results | 24/24 passed |
| Commit hash | `dd9a580` |

### Session test corrections (commit `204b9b0`)

| Field | Value |
|-------|-------|
| Fix | Corrected `back/tests/test_session_unit.py` for D1–D4 audit findings |
| Root cause | `Session.is_active` in SQLAlchemy 2.0+ does not indicate whether `Session.close()` has been called — it remains `True` after close(). It reflects connection/transaction state, not closure state. |
| Fix approach | Changed all 4 assertions from `session.is_active is False` to `not session.in_transaction()`. `in_transaction()` returns `False` after `close()` because the transaction is ended, which correctly verifies that cleanup terminates any active transaction. |
| D1 | `TestSessionLifecycle::test_session_can_be_closed`: `assert session.is_active is False` → `assert not session.in_transaction()` |
| D2 | `TestSessionCleanup::test_get_db_closes_session_after_exhaustion`: `assert session.is_active is False` → `assert not session.in_transaction()` |
| D3 | `TestSessionCleanup::test_get_db_closes_session_on_exception`: `assert session.is_active is False` → `assert not session.in_transaction()` |
| D4 | `TestFastApiDependency::test_get_db_yields_single_session`: `assert sessions[0].is_active is False` → `assert not sessions[0].in_transaction()` |
| Files changed | `back/tests/test_session_unit.py` |
| Focused test results | 4/4 passed |
| Full file results | 16/16 passed |
| Full suite results | 332 collected, 323 passed, 5 failed (all pre-existing database B1/B4-B7), 9 skipped |
| Commit hash | `204b9b0` |

### Database engine configuration test corrections (commit `f222067`)

| Field | Value |
|-------|-------|
| Fix | Corrected `back/tests/test_database_unit.py` for B1 and B4–B7 audit findings |
| B1 | `test_create_db_engine_raises_value_error_when_url_is_empty`: Added `monkeypatch.setattr(database.settings, 'DATABASE_URL', '')` to isolate settings from developer's `.env` file, matching the sibling test's isolation pattern |
| B4–B7 | Changed `sqlite:///:memory:` to `postgresql+psycopg://user:pass@localhost:5432/test_db` in four pool configuration tests. Each now verifies `QueuePool` type via `isinstance(engine_instance.pool, QueuePool)` and asserts pool parameters (`pool_size=5`, `max_overflow=10`, `pool_timeout=30`, `pool_recycle=1800`). Each engine is disposed in `try/finally`. |
| Files changed | `back/tests/test_database_unit.py` |
| Focused test results | B1: 1/1 passed; B4–B7: 4/4 passed |
| Full file results | 16/16 passed |
| Full suite results | 332 collected, 328 passed, 0 failed, 9 skipped |
| Commit hash | `f222067` |

### Orders Unit 1: Database Migration + SQLAlchemy Models (commits `a0a3c81`, `495f520`, `a2a43c6`)

| Field | Value |
|-------|-------|
| Completed unit | Orders database migration + SQLAlchemy models + model unit tests |
| Files affected | `back/src/core/models/order.py` (new), `back/src/core/models/product.py` (modified), `back/src/core/models/__init__.py` (modified), `back/alembic/versions/8e7f6d5c4b3a_add_order_and_payment_tables.py` (new), `back/src/core/orders/tests/test_order_models_unit.py` (new), `back/src/core/orders/__init__.py` (new), `back/src/core/orders/tests/__init__.py` (new) |
| Models created | Order, OrderItem, OrderSubitem, Payment, Commission |
| Product changes | Added `reserved_quantity` Integer NOT NULL default 0; CHECK constraints: stock >= 0, reserved_quantity >= 0, reserved_quantity <= stock |
| Test results | 70/70 order model tests pass; full suite: 398 passed, 0 failed, 9 skipped |
| Commit hashes | `a0a3c81` (models), `495f520` (migration), `a2a43c6` (tests) |
| Observations | Orders module database schema complete. Orders RESTRICT references users (preserves order history on user deletion). Order items snapshot product_name, product_sku, price. Order subitems have UNIQUE(order_id, seller_id). Payments and commissions have unique idempotency constraints. Product.reserved_quantity tracks stock reserved for pending orders. Available stock = stock - reserved_quantity. |
| Migration | Revision `8e7f6d5c4b3a`, parent `7f3a1e2c4d8b`. Creates: orders, order_items, order_subitems, payments, commissions. Adds reserved_quantity to products with 3 CHECK constraints. Downgrade reverses all changes. Migration applied to `plataforma_comercio_dev`. |

### Orders Unit 2a: Order and OrderItem Repositories (commit `b777629`)

| Field | Value |
|-------|-------|
| Completed unit | Orders repository layer - OrderRepository and OrderItemRepository |
| Files affected | `back/src/core/orders/repositories.py` (new), `back/src/core/orders/tests/test_order_repositories_unit.py` (new) |
| Repository classes | OrderRepository, OrderItemRepository |
| OrderRepository methods | get_by_id(order_id), get_by_user_id(user_id, skip, limit), get_by_user_and_idempotency_key(user_id, idempotency_key), add(order), delete(order) |
| OrderItemRepository methods | get_by_id(order_item_id), get_by_order_id(order_id), add(item), delete(item) |
| Transaction rules | No commit()/rollback()/refresh() in repositories. Service layer owns transaction boundaries. |
| Test results | 14/14 order repository tests pass; full suite: 412 passed, 0 failed, 9 skipped |
| Commit hash | `b777629` |
| Observations | Repository pattern follows CartRepository conventions. OrderRepository.get_by_id eagerly loads items with products via joinedload. OrderRepository.get_by_user_id supports pagination (skip/limit) and user isolation. OrderRepository.get_by_user_and_idempotency_key scopes lookup by both user_id and idempotency_key. OrderItemRepository.get_by_order_id scopes by order_id. No commit/rollback/refresh methods in repositories. |
| Last updated | 2026-11-25 |

### Orders Unit 2b.1: OrderSubitemRepository (commit `1f9c221`)

| Field | Value |
|-------|-------|
| Completed unit | Orders repository layer - OrderSubitemRepository |
| Files affected | `back/src/core/orders/repositories.py` (modified), `back/src/core/orders/tests/test_order_subitem_repository_unit.py` (new) |
| Repository class | OrderSubitemRepository |
| OrderSubitemRepository methods | get_by_id(order_subitem_id), get_by_order_id(order_id), get_by_order_and_seller(order_id, seller_id), add(subitem), delete(subitem) |
| Transaction rules | No commit()/rollback()/refresh() in repositories. Service layer owns transaction boundaries. |
| Test results | 7/7 order subitem repository tests pass; full suite: 419 passed, 0 failed, 9 skipped |
| Commit hash | `1f9c221` |
| Observations | Follows CartRepository conventions without commit()/rollback()/refresh() methods. OrderSubitemRepository.get_by_id retrieves subitem by ID. OrderSubitemRepository.get_by_order_id supports querying all subitems for an order. OrderSubitemRepository.get_by_order_and_seller scopes lookup by both order_id and seller_id. All persistence via self.db.add()/self.db.delete() only. |
| Last updated | 2026-11-25 |

### Orders Unit 2b.2: PaymentRepository (commit `6d55817`)

| Field | Value |
|-------|-------|
| Completed unit | Orders repository layer - PaymentRepository |
| Files affected | `back/src/core/orders/repositories.py` (modified), `back/src/core/orders/tests/test_payment_repository_unit.py` (new) |
| Repository class | PaymentRepository |
| PaymentRepository methods | get_by_id(payment_id), get_by_order_id(order_id), get_by_order_and_idempotency_key(order_id, idempotency_key), add(payment), delete(payment) |
| Transaction rules | No commit()/rollback()/refresh() in repositories. Service layer owns transaction boundaries. |
| Test results | 8/8 payment repository tests pass; full suite: 427 passed, 0 failed, 9 skipped |
| Commit hash | `6d55817` |
| Observations | Follows CartRepository conventions without commit()/rollback()/refresh() methods. PaymentRepository.get_by_id retrieves payment by ID. PaymentRepository.get_by_order_id supports querying all payments for an order. PaymentRepository.get_by_order_and_idempotency_key scopes lookup by both order_id and idempotency_key. All persistence via self.db.add()/self.db.delete() only. |
| Last updated | 2026-11-25 |

### Orders Unit 2b.3: CommissionRepository (commit 7ce7207)

| Field | Value |
|-------|-------|
| Completed unit | Orders repository layer - CommissionRepository |
| Files affected | ack/src/core/orders/repositories.py (modified), ack/src/core/orders/tests/test_commission_repository_unit.py (new) |
| Repository class | CommissionRepository |
| CommissionRepository methods | get_by_id(commission_id), get_by_seller_id(seller_id, skip, limit), get_by_order_subitem_id(order_subitem_id), add(commission), delete(commission) |
| Transaction rules | No commit()/rollback()/refresh() in repositories. Service layer owns transaction boundaries. |
| Test results | 8/8 commission repository tests pass; full suite: 435 passed, 0 failed, 9 skipped |
| Commit hash | 7ce7207 |
| Observations | Follows CartRepository conventions without commit()/rollback()/refresh() methods. CommissionRepository.get_by_id retrieves commission by ID. CommissionRepository.get_by_seller_id supports pagination (skip/limit) and seller isolation. CommissionRepository.get_by_order_subitem_id retrieves commission by subitem ID. All persistence via self.db.add()/self.db.delete() only. |






### Orders Unit 2b.4: ProductInventoryRepository (commit `064749f`)

| Field | Value |
|-------|-------|
| Completed unit | Orders repository layer - ProductInventoryRepository |
| Files affected | `back/src/core/orders/repositories.py` (modified), `back/src/core/orders/tests/test_product_inventory_repository_unit.py` (new) |
| Repository class | ProductInventoryRepository |
| ProductInventoryRepository methods | lock_products(product_ids), check_available_stock(product, quantity), reserve_quantity(product, quantity), release_reservation(product, quantity), confirm_consumption(product, quantity) |
| Transaction rules | No commit()/rollback()/refresh() in repositories. Service layer owns transaction boundaries. |
| Test results | 22/22 product inventory repository tests pass; full suite: 435 passed, 0 failed, 9 skipped |
| Commit hash | `064749f` |
| Observations | Follows CartRepository conventions without commit()/rollback()/refresh() methods. lock_products uses SELECT FOR UPDATE with ascending product_id ordering and deduplication. Available stock = stock - reserved_quantity. reserve_quantity increases reserved_quantity. release_reservation decreases reserved_quantity (never negative). confirm_consumption decreases both stock and reserved_quantity. Errors raised for missing products, invalid quantities, insufficient stock, insufficient reserved_quantity. |
| Last updated | 2026-11-25 |

