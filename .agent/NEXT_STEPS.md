# NEXT_STEPS.md

## Orders Unit 3a — Complete (all 5 units + corrections)

### Unit 3a.1 — Order model migration + source_cart_id/request_fingerprint — Commit `241b4a5`
- Added `source_cart_id: String(36)` (nullable, no FK) and `request_fingerprint: String(64)` (nullable, no FK) to `Order` model
- Alembic migration `0e9ed90dea55` created but NOT applied

### Unit 3a.2 — StoreRepository — Commit `363a36d`
- `get_seller_id(store_id)` and `get_seller_ids(store_ids)` bulk lookup
- No transaction methods in repository

### Unit 3a.3 — Cart concurrency coordination — Commit `0ecb5d4`
- `CartRepository.get_by_id_for_update()` with SELECT FOR UPDATE
- Cart row locking in add_item/update_item/remove_item

### Unit 3a.4 — Orders exceptions + fingerprint utility — Commit `f5e9065`
- Exception hierarchy, IdempotencyConflictError for HTTP 409
- Deterministic SHA-256 fingerprint utility

### Unit 3a.5 — OrderService.create_order_from_cart() — Commit `9f5b245` (includes P1+P2)
- Full transactional order creation flow
- P1: IntegrityError discrimination by constraint name
- P2: Removed pre-try-block rollbacks

### P3 Correction — Inventory stock guard — Commit `01a38ac`
- `reserve_quantity()` validates `reserved_quantity + quantity <= product.stock`

## Orders Unit 3b.1 — Pydantic API Schemas — Commit `a9536a0`

### Completed
- `back/src/core/orders/schemas.py` — new file with 6 schemas:
  - `OrderCreateRequest` — cart_id only (idempotency key via header)
  - `OrderItemResponse` — line item with price snapshot, nullable product_sku
  - `OrderSubitemResponse` — seller sub-order with subtotal
  - `OrderSummaryResponse` — lightweight listing (no nested items/subitems)
  - `OrderResponse` — full detail with items + subitems, excludes request_fingerprint
  - `OrderListResponse` — paginated list of summaries
- Decimal for all monetary fields; JSON serialization as decimal strings
- UUID types for IDs; timezone-aware datetime
- from_attributes ORM compatibility on response schemas
- ge=0 on monetary fields; gt=0 on quantities

### Test results
- `back/src/core/orders/tests/test_order_schemas_unit.py` — 25/25 passed
- Full suite: 597 passed, 0 failed, 9 skipped (PostgreSQL integration tests skipped)

**Next: Unit 3b.2 — OrderService retrieval methods** (get_order_by_id, list_orders_by_user, get_order_items, get_order_subitems) — required before GET endpoints can be implemented.
