# NEXT_STEPS.md

## Orders Unit 3a.1 — OrderService Foundation and Order Creation — Complete (commit `241b4a5`)

**Database migration and model updates — Complete.**
- Added `source_cart_id: String(36)` (nullable, no FK) to `Order` model in `back/src/core/models/order.py`.
- Added `request_fingerprint: String(64)` (nullable, no FK) to `Order` model.
- Created Alembic migration `0e9ed90dea55` (revises `8e7f6d5c4b3a`) adding both nullable columns to `orders` table.
- Migration created but NOT applied to any database.
- Added model unit tests (`test_order_source_cart_fingerprint_unit.py`) and migration unit tests (`test_order_migration_unit.py`).
- Full suite: 483 passed, 9 skipped, 0 failed.

## Orders Unit 3a.2 — StoreRepository — Complete (commit pending)

**StoreRepository — Complete.**
- Added `StoreRepository` to `back/src/core/orders/repositories.py` with:
  - `get_seller_id(store_id)` — single store lookup, returns seller ID or None.
  - `get_seller_ids(store_ids)` — bulk lookup returning dict mapping store_id -> seller_id, avoids N+1.
- Added Store model import to repositories.py.
- No commit/rollback/refresh methods (transaction boundary owned by service layer).
- Added focused unit tests (`test_store_repository_unit.py`): 10/10 pass.
- Full suite: 493 passed, 0 failed, 9 skipped.

**Next: Unit 3a.3 — Cart concurrency coordination**
- Add parent Cart row locking (`with_for_update()`) to `CartService.add_item()`, `update_item()`, `remove_item()`.
- Preserve existing ownership and product validation.
- Do not change normal read behavior.
- Add tests where test database supports it.

**Next: Unit 3a.4 — Orders exceptions and fingerprint utility**
- Orders-specific exception hierarchy (idempotency conflict mapped to HTTP 409).
- Deterministic Decimal normalization + SHA-256 fingerprint utility.
- Tests for reordered items, changed quantities, changed prices, different cart IDs.

**Next: Unit 3a.5 — OrderService creation flow**
- Implement `OrderService.create_order_from_cart()` only, per approved transaction sequence.
- Add focused unit and integration tests.
