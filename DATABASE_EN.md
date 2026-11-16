# DATABASE.md

## Main entities envisaged

### 1. users (users)
**ID**: user_id (PK)
**Attributes**: username, email, password_hash, is_seller, is_verified, created_at, last_login_at, preferences_json
**Responsibilities**: Base authentication, shared profile data for buyers and sellers, account configuration

### 2. sellers (sellers)
**ID**: seller_id (PK, FK towards users)
**Attributes**: store_name, business_name, tax_id, payment_info_json, bank_account, is_verified, created_at, last_login_at
**Responsibilities**: Seller registration, business configuration, accounting isolation, payment data (simulated)

### 3. stores (stores)
**ID**: store_id (PK)
**Attributes**: seller_id (FK), name, description, slug, logo_url, cover_image_url, is_active, created_at, updated_at
**Responsibilities**: Store administration, storefront page, images, store configuration

### 4. categories (categories)
**ID**: category_id (PK)
**Attributes**: name, description, slug, parent_id, level, path, is_active, created_at
**Responsibilities**: Product catalog organization, hierarchy, label management

### 5. products (products)
**ID**: product_id (PK)
**Attributes**: store_id (FK), category_id (FK), name, description, price, cost, sku, stock, is_active, images_urls, created_at, updated_at
**Responsibilities**: Product catalog, inventory management, pricing, images

### 6. carts (carts)
**ID**: cart_id (PK)
**Attributes**: user_id (FK), created_at, expires_at, last_updated_at
**Responsibilities**: Temporary shopping management, cross-device synchronization

### 7. cart_items (cart_items)
**ID**: cart_item_id (PK)
**Attributes**: cart_id (FK), product_id (FK), quantity, price_at_time, created_at
**Responsibilities**: Product management in cart, price calculation, quantity tracking

### 8. orders (orders)
**ID**: order_id (PK)
**Attributes**: user_id (FK), total_amount, status, payment_status, created_at, updated_at
**Responsibilities**: Main order, total calculation, status tracking, commission calculation

### 9. order_items (order_items)
**ID**: order_item_id (PK)
**Attributes**: order_id (FK), product_id (FK), quantity, price, seller_id, created_at
**Responsibilities**: Individual order items, seller assignment, sub-order calculation

### 10. order_subitems (order_subitems)
**ID**: order_subitem_id (PK)
**Attributes**: order_id (FK), seller_id, subtotal, commission, status, created_at
**Responsibilities**: Sub-order calculation, seller commission calculation, individual status tracking

### 11. payments (payments)
**ID**: payment_id (PK)
**Attributes**: order_id (FK), amount, method, status, transaction_id, processed_at, created_at
**Responsibilities**: Simulated payment processing, transaction recording, refund tracking

### 12. commissions (commissions)
**ID**: commission_id (PK)
**Attributes**: seller_id (FK), order_subitem_id (FK), amount, status, paid_at, created_at
**Responsibilities**: Commission calculation and tracking, payment recording to sellers

### 13. product_reviews (product_reviews)
**ID**: review_id (PK)
**Attributes**: product_id (FK), user_id (FK), rating, title, content, is_approved, created_at, updated_at
**Responsibilities**: Product reviews, rating system, content moderation

### 14. store_reviews (store_reviews)
**ID**: store_review_id (PK)
**Attributes**: store_id (FK), user_id (FK), rating, title, content, is_approved, created_at, updated_at
**Responsibilities**: Store reviews, storefront rating, content moderation

### 15. inventories (inventories)
**ID**: inventory_id (PK)
**Attributes**: product_id (FK), store_id (FK), quantity, reserved_quantity, last_updated_at
**Responsibilities**: Stock control, quantity tracking, availability validation

### 16. notifications (notifications)
**ID**: notification_id (PK)
**Attributes**: user_id (FK), title, message, type, is_read, related_entity_type, related_entity_id, created_at
**Responsibilities**: Notification system, system alerts, confirmations

### 17. payment_credentials (payment_credentials)
**ID**: credential_id (PK)
**Attributes**: seller_id (FK), provider, card_data_encrypted, is_default, created_at, updated_at
**Responsibilities**: Payment card management, encrypted data (simulated)

## Entity relationships

### One-to-many relationships
- **users → sellers**: A user can be a seller (optional), FK seller_id in users
- **users → orders**: A user can have multiple orders, FK user_id in orders
- **users → carts**: A user can have multiple active carts, FK user_id in carts
- **users → product_reviews**: A user can write multiple reviews, FK user_id in product_reviews
- **users → store_reviews**: A user can write multiple store reviews, FK user_id in store_reviews
- **users → notifications**: A user receives multiple notifications, FK user_id in notifications
- **sellers → stores**: A seller can have multiple stores, FK seller_id in stores
- **sellers → commissions**: A seller receives multiple commissions, FK seller_id in commissions
- **sellers → payment_credentials**: A seller saves multiple payment methods, FK seller_id in payment_credentials
- **stores → products**: A store can have multiple products, FK store_id in products
- **stores → store_reviews**: A store receives multiple reviews, FK store_id in store_reviews
- **stores → inventories**: A store maintains inventory for products, FK store_id in inventories
- **stores → notifications**: A store can receive notifications, FK store_id in notifications
- **categories → products**: A category can have multiple products, FK category_id in products
- **categories → subcategories**: Category hierarchy, self-relationship via parent_id
- **products → cart_items**: A product can be in multiple carts, FK product_id in cart_items
- **products → order_items**: A product can appear in multiple orders, FK product_id in order_items
- **products → product_reviews**: A product receives multiple reviews, FK product_id in product_reviews
- **products → inventories**: A product has inventory in stores, FK product_id in inventories
- **carts → cart_items**: A cart has multiple items, FK cart_id in cart_items
- **orders → order_items**: An order has multiple items, FK order_id in order_items
- **orders → payments**: An order has a payment, FK order_id in payments
- **orders → order_subitems**: An order has multiple sub-orders, FK order_id in order_subitems
- **orders → notifications**: An order can generate notifications, FK order_id in notifications
- **order_subitems → commissions**: A sub-order generates a commission, FK order_subitem_id in commissions
- **order_subitems → notifications**: A sub-order can generate notifications, FK order_subitem_id in notifications

### Many-to-many relationships (implicit)
- **products ↔ users (via product_reviews)**: A product receives reviews from multiple users
- **stores ↔ users (via store_reviews)**: A store receives reviews from multiple users

## Responsibilities of each entity

### Core business entities
- **products**: Product catalog development, inventory management, pricing definition
- **orders**: Purchase lifecycle management, total calculation, financial tracking
- **sellers**: Business registration and verification, store administration

### Supporting entities
- **users**: Base authentication, profiles, preferences
- **stores**: Storefront presence, branding, configuration
- **categories**: Catalog organization, navigation

### Transactional entities
- **carts**: Temporary shopping management, real-time price calculations
- **cart_items**: Product selection details, subtotal calculation

### Financial entities
- **payments**: Transaction processing, refund tracking
- **commissions**: Payment calculation to sellers, accounting

### Quality controls
- **inventories**: Stock control, availability validation
- **product_reviews**: User feedback, rating system
- **store_reviews**: Store reputation, service quality

### Interaction
- **notifications**: User communication, system alerts
- **payment_credentials**: Simulated payment card management

## Considerations for multi-vendor orders and inventory

### Data isolation between sellers
- **Inventory by store**: Each store maintains its own inventory for its products
- **Sub-orders by seller**: Orders are divided into sub-orders by seller for isolated accounting
- **Commissions by sub-order**: Commissions are calculated per sub-order, not per complete order
- **Seller-specific products**: Relationships `products.store_id` and `inventories.store_id` ensure sellers only see and manage their own products

### Inventory control
- **inventories** maintains quantities per product and store
- **products** maintains general stock per product (future project)
- **cart_items** validates availability in real time
- **order_items** reserves quantities when creating order
- **inventories** updates quantities after order completion

### Data deduplication
- **products** stores master information (once per product)
- **inventories** stores quantities per store (many-to-one)
- **cart_items** stores temporary prices and quantities
- **order_items** stores price snapshots per order (historical)

### Inventory control flow
1. **Validation in cart**: `cart_items` validates availability by consulting `inventories`
2. **Reservation when creating order**: `order_items` reserves quantities in `inventories`
3. **Delivery**: `order_items` decreases quantities in `inventories`
4. **Cancellation**: `order_items` returns quantities from `inventories`

### Commission isolation
- **order_subitems** calculates commissions per seller per order
- **commissions** tracks individual payments by seller_id
- Calculation: `commissions.amount = subtotal * commission_percentage`
- Payment: `commissions.paid_at` marks as paid when processed

### Future planning for scalability
- **Distributed inventory**: Each store handles its own inventory locally
- **Commission calculation**: By backend, validating client before creation
- **Seller billing**: Isolated calculations by seller_id
- **Cross-seller transfers**: Future system for shared inventory

## Data consolidation points

### Seller statistics
- Join of `order_subitems` by seller_id for total revenue
- Join with `commissions` for payment tracking
- Join with `products` for count of items sold

### Cart analysis
- `cart_items` + `products` for subtotal calculation
- `carts` + `users` for user behavior

### Financial auditing
- Join of `orders` + `payments` + `commissions` + `sellers`
- Trace each sub-order to its commission

## Referential integrity constraints

- **ON DELETE CASCADE**: 
  - `ON DELETE CASCADE` in `products.store_id` → `stores.store_id`
  - `ON DELETE CASCADE` in `inventories.store_id` → `stores.store_id`
  - `ON DELETE CASCADE` in `inventories.product_id` → `products.product_id`
  - `ON DELETE CASCADE` in `store_reviews.store_id` → `stores.store_id`
  - `ON DELETE CASCADE` in `product_reviews.product_id` → `products.product_id`

- **ON DELETE RESTRICT**:
  - `ON DELETE RESTRICT` in `order_items.seller_id` → `sellers.seller_id` (prevents accidental deletion)
  - `ON DELETE RESTRICT` in `commissions.seller_id` → `sellers.seller_id`
  - `ON DELETE RESTRICT` in `commissions.order_subitem_id` → `order_subitems.order_subitem_id`

## Future notes
- No need to write SQL yet (according to requirement)
- Migrations will be added when implementing entities
- Indexes will be added for frequent queries
- Support for soft deletes will be added
- Change auditing will be added
- Schema version control will be added
