# NEXT_STEPS.md

## Orders Unit 3a.1 — OrderService Foundation and Order Creation — Complete (commit pending)

**Database migration and model updates — Complete.**
- Added `source_cart_id: String(36)` (nullable, no FK) to `Order` model in `back/src/core/models/order.py`.
- Added `request_fingerprint: String(64)` (nullable, no FK) to `Order` model.
- Created Alembic migration `0e9ed90dea55` (revises `8e7f6d5c4b3a`) adding both nullable columns to `orders` table.
- Migration created but NOT applied to any database.
- Added model unit tests (`test_order_source_cart_fingerprint_unit.py`) and migration unit tests (`test_order_migration_unit.py`).
- Full suite: 483 passed, 9 skipped, 0 failed.

**Next: Unit 3a.2 — StoreRepository**
- Implement `StoreRepository.get_seller_id()` or equivalent bulk method to retrieve seller IDs for stores associated with order products.
- Avoid N+1 queries with bulk lookup.
- Add focused unit tests.
- Commit independently.

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
