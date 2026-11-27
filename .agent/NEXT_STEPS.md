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

## Orders Unit 3b.2 — OrderService Retrieval Methods — Commit `2f865a7`

### Completed
- `back/src/core/orders/services.py` — added 4 read-only retrieval methods:
  - `get_order_by_id(order_id, current_user)` — buyer or admin access, raises OrderNotFoundError/OrderOwnershipError
  - `list_orders_by_user(current_user, skip, limit)` — paginated listing with total count
  - `get_order_items(order_id, current_user)` — items after parent order authorization check
  - `get_order_subitems(order_id, current_user)` — subitems after parent order authorization check
- `back/src/core/orders/repositories.py` — added:
  - `count_by_user_id(user_id)` — count for pagination metadata
  - `get_by_id()` now eagerly loads subitems (joinedload) to avoid N+1

### Corrections
- Correction 1 (commit `6de6658`): Added integration tests proving `get_by_id()` returns complete items and subitems collections. Verified `.unique()` is NOT required for `Session.query()` legacy API in SQLAlchemy 2.0 — the Query object internally handles result merging. `.unique()` is only needed on `Result` objects from `Session.execute()`.
- Correction 2 (commit `c96b6c0`): Added `Order.order_id.desc()` as stable secondary sort key to `get_by_user_id()` for deterministic pagination ordering.

### Authorization
- Buyers access only their own orders (`order.user_id == current_user.user_id`)
- Administrators can access any order (`current_user.is_admin`)
- Sellers cannot access orders merely because they have products in them
- All methods are read-only - no commit/rollback/refresh

### Test results
- `back/src/core/orders/tests/test_order_service_retrieval_unit.py` — 22/22 passed
- `back/src/core/orders/tests/test_order_repositories_unit.py` — 18/18 passed (15 existing + 4 new)
- Full suite: 623 passed, 0 failed, 9 skipped (PostgreSQL integration tests skipped)

## Orders Unit 3b.4 — Orders API Router — Commit `47d9fc3`

### Completed
- `back/src/core/orders/router.py` — Orders HTTP router with 5 endpoints:
  - POST /orders/ — Create order from cart (201 on success, 200 on idempotent retry)
  - GET /orders/{order_id} — Retrieve order by ID (buyer or admin only)
  - GET /orders/ — List authenticated user's orders (paginated)
  - GET /orders/{order_id}/items — Retrieve order line items
  - GET /orders/{order_id}/subitems — Retrieve order seller subitems
- `back/src/main.py` — Registered orders router under /api/v1 prefix
- UUID validation returns 404 to avoid information disclosure
- ORM objects converted to Pydantic response schemas before returning
- Decimal monetary values serialize as decimal strings
- Reuses _handle_service_error() for consistent exception-to-HTTP mapping

### Test results
- `back/src/core/orders/tests/test_order_router_unit.py` — 20/20 passed
- Full suite: 670 passed, 0 failed, 9 skipped (PostgreSQL integration tests skipped)

**All Orders Unit 3b work is complete (3b.1 through 3b.4).**

**Next: PostgreSQL row-lock semantics verification** (SQLite only, no live PostgreSQL available) or proceed to Unit 3b.5 if authorized.
