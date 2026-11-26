# NEXT_STEPS.md

## Orders Unit 3a.1 — OrderService Foundation and Order Creation — Complete (commit `241b4a5`)

**Database migration and model updates — Complete.**
- Added `source_cart_id: String(36)` (nullable, no FK) to `Order` model in `back/src/core/models/order.py`.
- Added `request_fingerprint: String(64)` (nullable, no FK) to `Order` model.
- Created Alembic migration `0e9ed90dea55` (revises `8e7f6d5c4b3a`) adding both nullable columns to `orders` table.
- Migration created but NOT applied to any database.
- Added model unit tests (`test_order_source_cart_fingerprint_unit.py`) and migration unit tests (`test_order_migration_unit.py`).
- Full suite: 483 passed, 9 skipped, 0 failed.

## Orders Unit 3a.2 — StoreRepository — Complete (commit `363a36d`)

**StoreRepository — Complete.**
- Added `StoreRepository` to `back/src/core/orders/repositories.py` with:
  - `get_seller_id(store_id)` — single store lookup, returns seller ID or None.
  - `get_seller_ids(store_ids)` — bulk lookup returning dict mapping store_id -> seller_id, avoids N+1.
- Added Store model import to repositories.py.
- No commit/rollback/refresh methods (transaction boundary owned by service layer).
- Added focused unit tests (`test_store_repository_unit.py`): 10/10 pass.
- Full suite: 493 passed, 0 failed, 9 skipped.

## Orders Unit 3a.3 — Cart concurrency coordination — Complete (commit pending)

**Cart row locking — Complete.**
- Added `CartRepository.get_by_id_for_update(cart_id)` — queries Cart with `SELECT ... FOR UPDATE` and joinedload for items+products.
- Added `CartService._get_locked_cart(cart_id, current_user)` — locks cart row, verifies existence and ownership.
- `CartService.add_item()` — locks cart row before reading/modifying items.
- `CartService.update_item()` — locks cart row before reading/modifying items.
- `CartService.remove_item()` — locks cart row before reading/modifying items.
- `CartService.get_cart()` — unchanged (no lock, normal read).
- Lock ordering: Cart row first (product row locks not needed for cart mutations).
- Added focused unit tests (`test_cart_locking_unit.py`): 12/12 pass.
- Updated existing cart item test mocks to include `with_for_update()` in query chain.
- Full suite: 505 passed, 0 failed, 9 skipped.
- PostgreSQL row-lock semantics NOT verified (SQLite only); documented limitation.

**Next: Unit 3a.4 — Orders exceptions and fingerprint utility**
- Orders-specific exception hierarchy (idempotency conflict mapped to HTTP 409).
- Deterministic Decimal normalization + SHA-256 fingerprint utility.
- Tests for reordered items, changed quantities, changed prices, different cart IDs.

**Next: Unit 3a.5 — OrderService creation flow**
- Implement `OrderService.create_order_from_cart()` only, per approved transaction sequence.
- Add focused unit and integration tests.
