# NEXT_STEPS.md

## Orders Unit 2b.4: ProductInventoryRepository — Complete (commit `064749f`)

**Orders Unit 2b.5: OrderService**

Create OrderService with transaction-boundary management:
- OrderService: create_cart_from_order (validate, reserve stock, create order, items, subitems, payments, commissions)
- OrderService: get_cart_by_id, get_cart_by_user_id
- OrderService: update_cart_status, update_cart_payment_status

Transaction boundary management: commit/rollback at service layer, not repository.
