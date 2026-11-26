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

## Orders Unit 3a.3 — Cart concurrency coordination — Complete (commit `0ecb5d4`)

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

## Orders Unit 3a.4 — Orders exceptions and fingerprint utility — Complete (commit `f5e9065`)

**Orders exceptions (`back/src/core/orders/exceptions.py`) — Complete.**
- `OrderError(Exception)` — base.
- `OrderNotFoundError(OrderError)` — takes order_id.
- `OrderOwnershipError(OrderError)` — takes order_id, user_id.
- `OrderItemNotFoundError(OrderError)` — takes order_item_id.
- `ProductNotFoundError(OrderError)` — takes product_id.
- `ProductInactiveError(OrderError)` — takes product_id.
- `InsufficientStockError(OrderError)` — takes product_id, requested, available.
- `IdempotencyConflictError(OrderError)` — takes message; distinguishable for HTTP 409 mapping.
- Cart exceptions NOT reused; independent of HTTP framework.

**Fingerprint utility (`back/src/core/orders/fingerprint.py`) — Complete.**
- `generate_cart_fingerprint(cart: Cart) -> str` — SHA-256 of canonical cart representation.
- Canonical input: cart_id + items sorted by product_id (product_id, quantity, price_at_time).
- Decimal normalized to fixed 2-place string via quantize; never float.
- JSON with sort_keys=True, compact separators; UTF-8 encoded.
- 64-char lowercase hex digest.
- Rejects non-Decimal monetary values.
- Independent of DB sessions and HTTP requests.
- Added focused unit tests (`test_order_exceptions_and_fingerprint_unit.py`): 28/28 pass.
- Full suite: 533 passed, 0 failed, 9 skipped.

## Orders Unit 3a.5 — OrderService creation flow — Complete (commit pending)

**OrderService.create_order_from_cart() — Complete.**
- `back/src/core/orders/services.py` — full transactional order creation flow.
- Transaction boundary owned by service layer (commit once, rollback on any failure).
- Cart row locked via `CartRepository.get_by_id_for_update()` before any item access.
- Products locked in ascending order via `ProductInventoryRepository.lock_products()`.
- Seller IDs resolved via `StoreRepository.get_seller_ids()` (bulk, no N+1).
- Inventory reserved via `ProductInventoryRepository.reserve_quantity()`.
- All monetary calculations use `Decimal`, never `float`.
- `CartItem.price_at_time` used as authoritative price snapshot.
- Cart remains intact after successful order creation.
- Idempotency: same user+key+cart+fingerprint returns existing order; changed cart/fingerprint raises `IdempotencyConflictError`.
- Concurrent IntegrityError on `(user_id, idempotency_key)` caught, rolled back, re-queried, fingerprint compared.
- No Payment or Commission creation.
- No cart clearing.
- 27 unit + integration tests (mock-based + SQLite).
- Full suite: 560 passed, 0 failed, 9 skipped.
- PostgreSQL concurrency tests NOT run (no live PostgreSQL database available).

**All Orders Unit 3a work is complete.** No further units in scope for this session.
