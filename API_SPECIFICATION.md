# API_SPECIFICATION.md

## REST API conventions

### Base format
- **Base URL**: `/api/v1/`
- **Prefix**: `/api/v1`
- **Content-Type**: `application/json` for all requests/responses
- **Endpoints**: Plural (e.g., `/users`, `/products`, `/orders`)
- **Query parameters**: Used for filtering, pagination, sorting
- **Path parameters**: Used for IDs (`/users/{user_id}`, `/products/{product_id}`)

### Versioning strategy
- **Minor version**: Increments when new resources are added or major API changes occur
- **Patch version**: Increments when changes are made to request/response models without breaking compatibility
- **URL scheme**: `/api/v1` (current), `/api/v2` (future if needed)
- **Version headers**: Not used, URL-based only

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
- **"NOT_FOUND"**: Resource not found
- **"INVALID_INPUT"**: Invalid request data
- **"UNAUTHORIZED"**: Insufficient permissions
- **"FORBIDDEN"**: Access prohibited
- **"CONFLICT"**: Conflict (e.g., duplicate, stock)
- **"VALIDATION_ERROR"**: Data validation error
- **"INTERNAL_ERROR"**: Unexpected server error

## Endpoint organization by modules

### Authentication module (`/api/v1/auth/`)
- `POST /api/v1/auth/register` (user registration)
- `POST /api/v1/auth/login` (login)
- `POST /api/v1/auth/logout` (logout)
- `GET /api/v1/auth/me` (current profile)
- `PUT /api/v1/auth/password` (password update)
- `POST /api/v1/auth/refresh` (token refresh)

### User module (`/api/v1/users/`)
- `GET /api/v1/users/{user_id}` (get user profile)
- `PUT /api/v1/users/{user_id}` (update profile)
- `DELETE /api/v1/users/{user_id}` (delete account)
- `GET /api/v1/users/{user_id}/orders` (user orders)

### Seller module (`/api/v1/sellers/`)
- `POST /api/v1/sellers/` (register new seller)
- `GET /api/v1/sellers/{seller_id}` (get seller)
- `PUT /api/v1/sellers/{seller_id}` (update seller)
- `GET /api/v1/sellers/{seller_id}/stores` (seller's stores)
- `GET /api/v1/sellers/{seller_id}/stats` (seller statistics)

### Store module (`/api/v1/stores/`)
- `POST /api/v1/stores/` (create store)
- `GET /api/v1/stores/{store_id}` (get store)
- `PUT /api/v1/stores/{store_id}` (update store)
- `DELETE /api/v1/stores/{store_id}` (delete store)
- `GET /api/v1/stores/{store_id}/products` (store's products)
- `GET /api/v1/stores/{store_id}/stats` (store statistics)

### Category module (`/api/v1/categories/`)
- `POST /api/v1/categories/` (create category)
- `GET /api/v1/categories/{category_id}` (get category)
- `PUT /api/v1/categories/{category_id}` (update category)
- `DELETE /api/v1/categories/{category_id}` (delete category)
- `GET /api/v1/categories/` (list categories with pagination)
- `GET /api/v1/categories/{category_id}/products` (category's products)

### Product module (`/api/v1/products/`)
- `POST /api/v1/products/` (create product)
- `GET /api/v1/products/{product_id}` (get product)
- `PUT /api/v1/products/{product_id}` (update product)
- `DELETE /api/v1/products/{product_id}` (delete product)
- `GET /api/v1/products/` (list products with filters)
- `GET /api/v1/products/search` (advanced search)
- `POST /api/v1/products/{product_id}/images` (upload image)
- `DELETE /api/v1/products/{product_id}/images/{image_id}` (delete image)

### Cart module (`/api/v1/carts/`)
- `POST /api/v1/carts/` (create cart)
- `GET /api/v1/carts/{cart_id}` (get cart)
- `PUT /api/v1/carts/{cart_id}` (update cart)
- `DELETE /api/v1/carts/{cart_id}` (delete cart)
- `POST /api/v1/carts/{cart_id}/items` (add item to cart)
- `PUT /api/v1/carts/{cart_id}/items/{item_id}` (update item)
- `DELETE /api/v1/carts/{cart_id}/items/{item_id}` (remove item)
- `POST /api/v1/carts/{cart_id}/validate` (validate cart)
- `POST /api/v1/carts/{cart_id}/merge/{guest_cart_id}` (merge carts)

### Order module (`/api/v1/orders/`)
- `POST /api/v1/orders/` (create order)
- `GET /api/v1/orders/{order_id}` (get order)
- `GET /api/v1/orders/` (list user's orders)
- `PUT /api/v1/orders/{order_id}/status` (update status)
- `POST /api/v1/orders/{order_id}/cancel` (cancel order)
- `GET /api/v1/orders/{order_id}/items` (order's items)
- `GET /api/v1/orders/{order_id}/subitems` (order's sub-orders)

### Payment module (`/api/v1/payments/`)
- `POST /api/v1/payments/` (process payment)
- `GET /api/v1/payments/{payment_id}` (get payment)
- `GET /api/v1/payments/{order_id}` (order's payments)
- `POST /api/v1/payments/{payment_id}/refund` (process refund)

### Commission module (`/api/v1/commissions/`)
- `GET /api/v1/commissions/{commission_id}` (get commission)
- `GET /api/v1/sellers/{seller_id}/commissions` (seller's commissions)
- `POST /api/v1/commissions/{commission_id}/mark-paid` (mark as paid)

### Review module (`/api/v1/reviews/`)
- `POST /api/v1/reviews/products` (create product review)
- `GET /api/v1/reviews/products/{product_id}` (product's reviews)
- `POST /api/v1/reviews/stores` (create store review)
- `GET /api/v1/reviews/stores/{store_id}` (store's reviews)
- `PUT /api/v1/reviews/{review_id}` (update review)
- `DELETE /api/v1/reviews/{review_id}` (delete review)

### Notification module (`/api/v1/notifications/`)
- `GET /api/v1/notifications/` (list notifications)
- `GET /api/v1/notifications/{notification_id}` (get notification)
- `PUT /api/v1/notifications/{notification_id}/read` (mark as read)
- `DELETE /api/v1/notifications/{notification_id}` (delete notification)

### Admin module (`/api/v1/admin/`)
- `GET /api/v1/admin/stats` (general statistics)
- `GET /api/v1/admin/users` (list users)
- `GET /api/v1/admin/sellers` (list sellers)
- `GET /api/v1/admin/orders` (list orders)
- `GET /api/v1/admin/revenue` (revenue statistics)
- `GET /api/v1/admin/inventory` (inventory audit)

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

### Request schemas (use Pydantic)
- **UUIDs**: ISO 8601 for datetime, UUID for IDs
- **Emails**: Standard format
- **Numbers**: Range validation (price, quantity)
- **Strings**: Maximum lengths, regex for slugs
- **Bools**: Standard boolean values

### Standard error messages
- **"REQUIRED_FIELD"**: Required field missing
- **"INVALID_FORMAT"**: Invalid format
- **"DUPLICATE_ENTRY"**: Duplicate entry
- **"INSUFFICIENT_STOCK"**: Insufficient stock
- **"UNAUTHORIZED_ACCESS"**: Insufficient permissions
- **"RATE_LIMIT_EXCEEDED"**: Rate limit exceeded

## Security points

### Authorization requirements
- **JWT**: Token in `Authorization: Bearer {token}` header
- **Seller isolation**: All routes involving stores validate seller_id
- **Role-based**: Some endpoints require specific roles

### Input validation
- **Request body**: Validated via Pydantic schemas
- **Path params**: Validated as UUIDs/strings
- **Query params**: Validated with appropriate ranges
- **Headers**: Validated (Authorization, Content-Type)

### Output validation
- **Sensitive fields**: Removed from responses (e.g., password_hash)
- **Filtered data**: Only appropriate data shown per role
- **Files**: S3 URLs, not binary data

## Protocols
Here
