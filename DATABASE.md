# DATABASE.md

## Main entities

| Entity | ID (PK) | Key attributes | Responsibilities |
|--------|---------|----------------|------------------|
| **users** | user_id | username, email, password_hash, is_seller, is_verified, is_admin, is_moderator, created_at, last_login_at, preferences_json | Base authentication, shared profile data for buyers and sellers |
| **sellers** | seller_id (FK → users) | store_name, business_name, tax_id, payment_info_json, bank_account, is_verified, created_at | Seller registration, business configuration, accounting isolation |
| **stores** | store_id | seller_id (FK), name, description, slug, logo_url, cover_image_url, is_active, created_at, updated_at | Store administration, storefront page, images |
| **categories** | category_id | name, description, slug, parent_id (FK → categories), level, path, is_active, created_at | Product catalog organization, category hierarchy |
| **products** | product_id | store_id (FK), category_id (FK), name, description, price, cost, sku, stock, reserved_quantity, is_active, images_urls, created_at, updated_at | Product catalog, inventory management, pricing |
| **carts** | cart_id | user_id (FK), created_at, expires_at, last_updated_at | Temporary shopping management |
| **cart_items** | cart_item_id | cart_id (FK), product_id (FK), quantity, price_at_time, created_at | Product selection in cart, price snapshots |
| **orders** | order_id | user_id (FK), total_amount, status, payment_status, idempotency_key, created_at, updated_at | Main order, total calculation, status tracking |
| **order_items** | order_item_id | order_id (FK), product_id (FK), quantity, price, seller_id, product_name, product_sku, created_at | Individual order items, seller assignment, price snapshots |
| **order_subitems** | order_subitem_id | order_id (FK), seller_id, subtotal, status, created_at | Sub-order calculation, seller accounting isolation |
| **payments** | payment_id | order_id (FK), amount, method, status, transaction_id, processed_at, idempotency_key, created_at | Simulated payment processing, refund tracking |
| **commissions** | commission_id | seller_id (FK), order_subitem_id (FK), amount, status, paid_at, created_at | Commission calculation and payment tracking |
| **product_reviews** | review_id | product_id (FK), user_id (FK), rating, title, content, is_approved, created_at, updated_at | Product reviews, rating system |
| **store_reviews** | store_review_id | store_id (FK), user_id (FK), rating, title, content, is_approved, created_at, updated_at | Store reviews, storefront rating |
| **notifications** | notification_id | user_id (FK), title, message, type, is_read, related_entity_type, related_entity_id, created_at | User notifications, system alerts |
| **payment_credentials** | credential_id | seller_id (FK), provider, card_data_encrypted, is_default, created_at, updated_at | Payment card management (simulated) |

## Entity relationships

### One-to-many relationships
- `users → sellers`: A user can optionally be a seller (FK `seller_id` in `users`)
- `users → orders`: A user can have multiple orders (FK `user_id` in `orders`)
- `users → carts`: A user can have multiple active carts (FK `user_id` in `carts`)
- `users → product_reviews`: A user can write multiple product reviews (FK `user_id` in `product_reviews`)
- `users → store_reviews`: A user can write multiple store reviews (FK `user_id` in `store_reviews`)
- `users → notifications`: A user receives multiple notifications (FK `user_id` in `notifications`)
- `sellers → stores`: A seller can have multiple stores (FK `seller_id` in `stores`)
- `sellers → commissions`: A seller receives multiple commissions (FK `seller_id` in `commissions`)
- `sellers → payment_credentials`: A seller saves multiple payment methods (FK `seller_id` in `payment_credentials`)
- `stores → products`: A store can have multiple products (FK `store_id` in `products`)
- `stores → store_reviews`: A store receives multiple reviews (FK `store_id` in `store_reviews`)
- `categories → products`: A category can have multiple products (FK `category_id` in `products`)
- `categories → categories`: Category hierarchy (self-relationship via `parent_id`)
- `products → cart_items`: A product can be in multiple carts (FK `product_id` in `cart_items`)
- `products → order_items`: A product can appear in multiple orders (FK `product_id` in `order_items`)
- `products → product_reviews`: A product receives multiple reviews (FK `product_id` in `product_reviews`)
- `carts → cart_items`: A cart has multiple items (FK `cart_id` in `cart_items`)
- `orders → order_items`: An order has multiple items (FK `order_id` in `order_items`)
- `orders → payments`: An order has a payment (FK `order_id` in `payments`)
- `orders → order_subitems`: An order has multiple sub-orders (FK `order_id` in `order_subitems`)
- `orders → notifications`: An order can generate notifications (FK `order_id` in `notifications`)
- `order_subitems → commissions`: A sub-order generates a commission (FK `order_subitem_id` in `commissions`)
- `order_subitems → notifications`: A sub-order can generate notifications (FK `order_subitem_id` in `notifications`)

### Many-to-many relationships (implicit)
- `products ↔ users` (via `product_reviews`)
- `stores ↔ users` (via `store_reviews`)

## Multi-vendor data isolation

- **Inventory by store**: Each store maintains inventory for its products through `products.store_id`
- **Sub-orders by seller**: Orders are divided into sub-orders per seller for isolated accounting
- **Commissions by sub-order**: Commissions are calculated per sub-order, not per complete order
- **Seller-specific products**: `products.store_id` ensures sellers only manage their own products

## Inventory control

- `products.stock` is the single source of truth for product stock quantities
- `products.reserved_quantity` tracks stock reserved for pending orders
- Available stock = `products.stock - products.reserved_quantity`
- `cart_items` validates availability in real time against `products.stock - products.reserved_quantity`
- `order_items` reserves quantities when creating an order by incrementing `products.reserved_quantity`
- **Payment confirmation**: `products.stock` decreases by `order_item.quantity` AND `products.reserved_quantity` decreases by `order_item.quantity` (never deduct full reserved_quantity)
- **Cancellation before payment**: `products.reserved_quantity` decreases by reserved amount (stock not yet deducted)
- **Cancellation after payment**: Stock already deducted at payment confirmation; no further stock change
- **Refund**: `products.stock` increases by refunded quantity

### Inventory control flow
1. **Cart validation**: `cart_items` checks availability against `products.stock - products.reserved_quantity`
2. **Order creation**: `order_items` reserves quantities by incrementing `products.reserved_quantity`
3. **Payment confirmation**: `products.stock` decreases by item quantity, `products.reserved_quantity` decreases by item quantity
4. **Cancellation (before payment)**: `products.reserved_quantity` decreases (stock not yet deducted)
5. **Cancellation (after payment)**: No further stock change (already deducted at payment)
6. **Refund**: `products.stock` increases by refunded quantity

## Commission model

- `commissions` table is the authoritative source of commission records and amounts
- `commission_id`: UUID primary key
- `seller_id`: FK → `sellers`, `ON DELETE RESTRICT`
- `order_subitem_id`: FK → `order_subitems`, `ON DELETE RESTRICT`
- `amount`: `Numeric(10,2)`, NOT NULL — authoritative commission amount
- `status`: defaults to `pending`
- `paid_at`: nullable timestamp
- `created_at`: timestamp
- Unique constraint on `order_subitem_id`, ensuring one commission per seller suborder

**`order_subitems` does NOT contain a commission field.** Commission data must not be duplicated.

### Commission data ownership rules

1. `commissions.amount` is the authoritative commission amount for a seller suborder.
2. `order_subitems` stores only `subtotal`, `status`, and relationships — never commission values.
3. When retrieving commission information for a seller suborder, use its relationship to the corresponding `commissions` record.
4. Do not introduce duplicate commission values across tables.
5. The initial MVP commission rate is 10%, but commission calculation and payment logic are outside the scope of Orders Unit 1 (database migration and models).

## CHECK constraints

- `products.stock >= 0`
- `products.reserved_quantity >= 0`
- `products.reserved_quantity <= stock`
- `order_items.quantity > 0`

## Indexes (TBD)
- Indexes for frequent queries TBD (e.g., `products.store_id`, `orders.user_id`, `orders.status`, `orders.payment_status`)

## Referential integrity constraints

### ON DELETE CASCADE
- `products.store_id` → `stores.store_id`
- `store_reviews.store_id` → `stores.store_id`
- `product_reviews.product_id` → `products.product_id`

### ON DELETE RESTRICT
- `orders.user_id` → `users.user_id` (preserves commercial order history)
- `order_items.seller_id` → `sellers.seller_id` (prevents accidental seller deletion)
- `order_items.product_id` → `products.product_id` (prevents accidental product deletion)
- `commissions.seller_id` → `sellers.seller_id`
- `commissions.order_subitem_id` → `order_subitems.order_subitem_id`

## Pending decisions (TBD)

- **Specific index definitions**: Which columns need indexes TBD
- **Trigger rules**: Database triggers for inventory consistency TBD
- **Soft delete support**: Whether to implement soft deletes TBD
- **Schema version control**: Alembic configured and tracking migrations
