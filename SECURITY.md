# SECURITY.md

## Authentication strategy

### JWT authentication
- **Algorithm**: RS256 (asymmetric)
- **Issuer**: `plataforma-comercio-server`
- **Audience**: `plataforma-comercio-frontend`
- **Access token expiry**: 15 minutes
- **Refresh token expiry**: 7 days
- **Refresh token**: Rotatable, stored in database
- **Revocation**: Local blacklist; revoked tokens invalidate access

### Authentication flow
1. **Registration**: Receive username, email, password; validate with Pydantic; hash password with Argon2; save to `users` table; return access_token + refresh_token
2. **Login**: Validate username/email + password; verify with Argon2; generate JWT access_token (15 min) + refresh_token (7 days); save refresh_token to database; return tokens
3. **Logout**: Invalidate refresh_token via blacklist; delete refresh_token from database
4. **Token validation**: Middleware verifies JWT in `Authorization: Bearer {token}` header; checks blacklist; extracts user_id and claims; loads user from database

### Password recovery
- **Flow**: `POST /api/v1/auth/forgot-password` + `POST /api/v1/auth/reset-password`
- **Rate limit**: 5 attempts per hour per IP
- **Recovery email**: Temporary token valid for 1 hour
- **Password change**: Invalidates previous tokens

## Authorization and roles

### User roles
- **user** (buyer): Base access; can buy, write reviews
- **seller** (vendor): Store management, products, orders, inventory
- **admin**: Complete system access
- **moderator**: Content administration, review moderation

### Role schema
```sql
users.is_seller BOOLEAN DEFAULT FALSE,
users.is_verified BOOLEAN DEFAULT FALSE,
users.is_admin BOOLEAN DEFAULT FALSE,
users.is_moderator BOOLEAN DEFAULT FALSE
```

### Role-based authorization
- **Protected routes**:
  - `POST /api/v1/sellers/`: Only non-vendor users can register
  - `PUT /api/v1/users/{user_id}`: Only own `user_id`
  - `GET/PUT /api/v1/sellers/{seller_id}`: Only the owner of the `seller_id`
  - `GET/PUT /api/v1/stores/{store_id}`: Only the owner of the `store_id`
  - `GET /api/v1/admin/`: Only administrators
  - `PUT /api/v1/orders/{order_id}/status`: Only admin or seller of the order

### Permission checking
- **Resource owner**: `user_id` from request == `resource.user_id`
- **Seller isolation**: `store.seller_id` == `request.seller_id` or `is_admin`
- **Admin override**: `is_admin` allows everything
- **Role-based**: `is_seller`, `is_moderator`, `is_admin` verified

## Password protection with Argon2

### Configuration
- **Algorithm**: argon2id
- **Hash format**: `$argon2id$v=19$m=65536,t=3,p=4$` + salt + hash
- **Salt**: Random per user, 16 bytes
- **Parameters**: Memory 64MB (65536 KB), iterations 3, parallelism 4, hash length 32 bytes

### Security rules
- No plaintext storage; only hash
- No salt reuse; generate random salt per user
- Rate limit: 5 login attempts per user per hour
- No user enumeration: do not indicate if email exists in registration
- High parameters to prevent GPU attacks

## JWT usage

### Token strategy
- **Access token**: Short-lived; content: `user_id, username, role, exp, iat`
- **Refresh token**: Long-lived; stored in database; random
- **Revocation**: Invalid refresh token allows revoking access without access token

### Validation
```python
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer)):
    # Decode and verify JWT
    # Load user from database
    # Return user
```

## Data isolation between sellers

### Database isolation
- **Row-level security (RLS)**: Each query filtered by appropriate `seller_id`
- **Row functions**: `is_seller_of_store(store_id)` returns bool
- **Policies**: RLS enabled with role-based restriction

### Module isolation
- **seller-module**: Only data of the owning seller
- **store-module**: Only stores of the seller
- **product-module**: Only products of the seller's stores
- **order-module**: Only orders/sub-orders of the seller's products
- **commission-module**: Only commissions of the seller

### Security scenarios
- Seller A cannot view Seller B's products or orders
- Admin can view everything (with audit restrictions)
- Seller can only modify their own data
- Users can only view products and create orders

## Input validation and information protection

### Input validation
- **Request body**: Validated via Pydantic schemas
- **Path params**: Validated as UUIDs/strings
- **Query params**: Validated with appropriate ranges
- **Headers**: Validated (Authorization, Content-Type)

### Input sanitization
- **SQL injection**: Prevented via SQLAlchemy ORM
- **XSS**: Prevented via HTML sanitization in frontend
- **CSRF**: JWT eliminates need for CSRF for API
- **Buffer overflow**: Prevented via input size validation

### Rate limiting
- **Global**: 100 requests per minute per IP
- **Login**: 5 attempts per user per hour
- **Register**: 1 attempt per email per hour
- **Password reset**: 3 attempts per user per hour

### Sensitive data protection
- **Password hash**: Argon2 with random salt
- **Payment data**: Tokenization in external payment services
- **Personal information**: Encryption in transit (HTTPS), encryption at rest (TLS)
- **Logs**: No logging of passwords, tokens, or payment data

### Audit and monitoring
- **Failed access attempts**: Log failed login attempts
- **Sensitive data**: Masked in logs (e.g., `email → us***@***.com`)
- **Data changes**: Log changes in important tables (users, orders)
- **Monitoring**: Detection of anomalous patterns (e.g., multiple failed logins)

### TLS and HTTPS
- **All endpoints**: HTTPS only in production
- **HSTS**: Implemented (`max-age: 31536000`)
- **Encryption**: TLS 1.2+, forward-secure ciphers
- **Certificates**: Let's Encrypt or corporate certificate

## Personal data protection

### GDPR/LGPD compliance
- **Consent**: Explicit consent required for personal data
- **Data access**: Endpoints for users to access/delete their data
- **Portability**: Export data in machine-readable JSON format
- **Retention**: Policies per regulations (e.g., users: 1 year, orders: 5 years)
- **Deletion**: Delete data within 30 days after account deletion

### Consent flow
1. **Registration**: Marketing consent (separate checkbox)
2. **Cookies**: Cookie banner with granular acceptance
3. **Email**: Double opt-in for promotional emails
4. **Third-party data**: No sharing without explicit consent

## Database security

### PostgreSQL configuration
- **SSL/TLS**: Mandatory for connections
- **Authentication**: Strong passwords, least privilege
- **Permissions**: Users with only necessary read/write permissions
- **Backups**: AES-256 encrypted, stored in S3
- **Monitoring**: Change auditing, access attempt detection

### Access control
- **Least privilege**: Each user/module has minimum necessary permissions
- **Role-based**: Specific users for operations
- **Row-level**: RLS for filtering rows by `seller_id`

## Pending decisions (TBD)

- **Refresh token storage**: Redis vs. database TBD
- **Rate limit exact values**: Per-endpoint limits TBD
- **File upload storage**: S3 or alternative TBD
- **Certificate provider**: Let's Encrypt vs. corporate TBD
