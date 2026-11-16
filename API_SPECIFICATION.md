# API_SPECIFICATION.md

## REST API conventions

### Base format
- **Base URL**: `/api/v1/`
- **Prefix**: `/api/v1`
- **Content-Type**: `application/json` for all requests/responses
- **Endpoints**: Plural nouns (e.g., `/users`, `/products`, `/orders`)
- **Query parameters**: Filtering, pagination, sorting
- **Path parameters**: Resource IDs (e.g., `/users/{user_id}`, `/products/{product_id}`)

### Versioning strategy
- **Minor version**: New resources or major API changes
- **Patch version**: Non-breaking changes to request/response models
- **URL scheme**: `/api/v1` (current); `/api/v2` TBD
- **Version headers**: Not used; URL-based only

### Standard response format
```json
{
  "success": true,
  "message": "string | null",
  "data": object | null,
  "timestamp": "ISO8601"
}
```

### Error response format
```json
{
  "success": false,
  "message": "string (descriptive error message)",
  "errors": [
    {
      "field": "string (specific field)",
      "message": "string (error description)",
      "code": "string (error code)"
    }
  ],
  "timestamp": "ISO8601"
}
```

### HTTP status codes
- **200 OK**: Successful request
- **201 CREATED**: Resource successfully created
- **400 BAD REQUEST**: Invalid request data
- **401 UNAUTHORIZED**: Not authenticated
- **403 FORBIDDEN**: Not authorized for this resource
- **404 NOT FOUND**: Resource not found
- **409 CONFLICT**: Conflict (e.g., insufficient stock)
- **500 INTERNAL SERVER ERROR**: Unexpected server error

### Common error codes
- `"NOT_FOUND"`: Resource not found
- `"INVALID_INPUT"`: Invalid request data
- `"UNAUTHORIZED"`: Insufficient permissions
- `"FORBIDDEN"`: Access prohibited
- `"CONFLICT"`: Conflict (e.g., duplicate, stock)
- `"VALIDATION_ERROR"`: Data validation error
- `"INTERNAL_ERROR"`: Unexpected server error

## Endpoint organization by modules

### Authentication module (`/api/v1/auth/`)
- `POST /register` — User registration
- `POST /login` — Login
- `POST /logout` — Logout
- `GET /me` — Current user profile
- `PUT /password` — Password update
- `POST /refresh` — Token refresh

### User module (`/api/v1/users/`)
- `GET /{user_id}` — Get user profile
- `PUT /{user_id}` — Update profile
- `DELETE /{user_id}` — Delete account
- `GET /{user_id}/orders` — User orders

### Seller module (`/api/v1/sellers/`)
- `POST /` — Register new seller
- `GET /{seller_id}` — Get seller
- `PUT /{seller_id}` — Update seller
- `GET /{seller_id}/stores` — Seller's stores
- `GET /{seller_id}/stats` — Seller statistics

### Store module (`/api/v1/stores/`)
- `POST /` — Create store
- `GET /{store_id}` — Get store
- `PUT /{store_id}` — Update store
- `DELETE /{store_id}` — Delete store
- `GET /{store_id}/products` — Store's products
- `GET /{store_id}/stats` — Store statistics

### Category module (`/api/v1/categories/`)
- `POST /` — Create category
- `GET /{category_id}` — Get category
- `PUT /{category_id}` — Update category
- `DELETE /{category_id}` — Delete category
- `GET /` — List categories with pagination
- `GET /{category_id}/products` — Category's products

### Product module (`/api/v1/products/`)
- `POST /` — Create product
- `GET /{product_id}` — Get product
- `PUT /{product_id}` — Update product
- `DELETE /{product_id}` — Delete product
- `GET /` — List products with filters
- `GET /search` — Advanced search
- `POST /{product_id}/images` — Upload image
- `DELETE /{product_id}/images/{image_id}` — Delete image

### Cart module (`/api/v1/carts/`)
- `POST /` — Create cart
- `GET /{cart_id}` — Get cart
- `PUT /{cart_id}` — Update cart
- `DELETE /{cart_id}` — Delete cart
- `POST /{cart_id}/items` — Add item to cart
- `PUT /{cart_id}/items/{item_id}` — Update item
- `DELETE /{cart_id}/items/{item_id}` — Remove item
- `POST /{cart_id}/validate` — Validate cart
- `POST /{cart_id}/merge/{guest_cart_id}` — Merge carts

### Order module (`/api/v1/orders/`)
- `POST /` — Create order
- `GET /{order_id}` — Get order
- `GET /` — List user's orders
- `PUT /{order_id}/status` — Update status
- `POST /{order_id}/cancel` — Cancel order
- `GET /{order_id}/items` — Order's items
- `GET /{order_id}/subitems` — Order's sub-orders

### Payment module (`/api/v1/payments/`)
- `POST /` — Process payment (simulated)
- `GET /{payment_id}` — Get payment
- `GET /{order_id}` — Order's payments
- `POST /{payment_id}/refund` — Process refund (simulated)

### Commission module (`/api/v1/commissions/`)
- `GET /{commission_id}` — Get commission
- `GET /sellers/{seller_id}/commissions` — Seller's commissions
- `POST /{commission_id}/mark-paid` — Mark commission as paid

### Review module (`/api/v1/reviews/`)
- `POST /products` — Create product review
- `GET /products/{product_id}` — Product's reviews
- `POST /stores` — Create store review
- `GET /stores/{store_id}` — Store's reviews
- `PUT /{review_id}` — Update review
- `DELETE /{review_id}` — Delete review

### Notification module (`/api/v1/notifications/`)
- `GET /` — List notifications
- `GET /{notification_id}` — Get notification
- `PUT /{notification_id}/read` — Mark as read
- `DELETE /{notification_id}` — Delete notification

### Admin module (`/api/v1/admin/`)
- `GET /stats` — General statistics
- `GET /users` — List users
- `GET /sellers` — List sellers
- `GET /orders` — List orders
- `GET /revenue` — Revenue statistics
- `GET /inventory` — Inventory audit

## Common filtering and query parameters

### General filtering
- `?search={term}`: Text search
- `?category={category_id}`: Filter by category
- `?store={store_id}`: Filter by store
- `?seller={seller_id}`: Filter by seller
- `?min_price={number}`: Minimum price
- `?max_price={number}`: Maximum price
- `?sort={field}:{order}`: Sort (e.g., `sort=price:desc`)
- `?limit={number}`: Result limit (default: 20)
- `?offset={number}`: Pagination offset

### Module-specific filtering

**Products:**
- `?in_stock=true/false`: Filter available products
- `?min_quantity={number}`: Minimum inventory quantity
- `?max_quantity={number}`: Maximum inventory quantity

**Orders:**
- `?status={status}`: Filter by status (pending, confirmed, cancelled, etc.)
- `?payment_status={status}`: Filter by payment status
- `?date_from={date}`: Filter orders from date
- `?date_to={date}`: Filter orders until date

**Reviews:**
- `?rating_min={number}`: Minimum rating
- `?rating_max={number}`: Maximum rating
- `?verified_only=true`: Only verified reviews

## Data validation formats

### Request schemas (Pydantic)
- **UUIDs**: ISO 8601 for datetime, UUID for IDs
- **Emails**: Standard format
- **Numbers**: Range validation (price, quantity)
- **Strings**: Maximum lengths, regex for slugs
- **Booleans**: Standard boolean values

### Standard error messages
- `"REQUIRED_FIELD"`: Required field missing
- `"INVALID_FORMAT"`: Invalid format
- `"DUPLICATE_ENTRY"`: Duplicate entry
- `"INSUFFICIENT_STOCK"`: Insufficient stock
- `"UNAUTHORIZED_ACCESS"`: Insufficient permissions
- `"RATE_LIMIT_EXCEEDED"`: Rate limit exceeded

## Security points

### Authorization requirements
- **JWT**: Token in `Authorization: Bearer {token}` header
- **Seller isolation**: Routes involving stores validate `seller_id`
- **Role-based**: Some endpoints require specific roles

### Input validation
- **Request body**: Validated via Pydantic schemas
- **Path params**: Validated as UUIDs/strings
- **Query params**: Validated with appropriate ranges
- **Headers**: Validated (Authorization, Content-Type)

### Output validation
- **Sensitive fields**: Removed from responses (e.g., `password_hash`)
- **Filtered data**: Only role-appropriate data shown

## Pending decisions (TBD)

- **API v2 migration**: Timing and breaking changes TBD
- **Rate limit configuration**: Exact limits per endpoint TBD
- **File upload storage**: S3 or alternative TBD
