# SECURITY.md

## Authentication strategy

### JWT authentication
- **Algorithm**: RS256 (symmetric, asymmetric)
- **Issuer**: The server (based on `ISS` config)
- **Audience**: Frontend (based on `AUD` config)
- **Duration**: 15 minutes (access), 7 days (refresh)
- **Refresh token**: Rotatable, stored in database
- **Revocation**: Local blacklist (Redis), revoked tokens invalidate access

### Authentication flow
1. **Registration (`/api/v1/auth/register`)**:
   - Receive username, email, password
   - Validate with Pydantic (e.g., email format, password length)
   - Hash password with Argon2 (argon2_id or argon2id)
   - Save in `users` table
   - Return access_token + refresh_token

2. **Login (`/api/v1/auth/login`)**:
   - Validate username/email + password
   - Verify password with Argon2
   - Generate JWT access_token (15min)
   - Generate JWT refresh_token (7days)
   - Save refresh_token in database
   - Return tokens

3. **Logout (`/api/v1/auth/logout`)`:
   - Invalidate refresh_token via blacklist
   - Delete refresh_token from database
   - Return success

4. **Token validation**:
   - Middleware intercepts all protected routes
   - Verify JWT in `Authorization: Bearer {token}` header
   - Verify in blacklist (if revoked)
   - Extract user_id and claims from token
   - Load user from database
   - Attach to request context

### Password recovery
- **Flow**: `POST /api/v1/auth/forgot-password` + `POST /api/v1/auth/reset-password`
- **Rate limit**: 5 attempts per hour per IP
- **Recovery email**: Temporary token (1 hour)
- **Password change**: Invalidates previous tokens
- **Secure tokens**: No reuse of previous tokens after password change

## Authorization and roles

### User roles
- **user** (buyer): Base access, can buy, write reviews
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
  - `PUT /api/v1/users/{user_id}`: Only own user_id
  - `GET/PUT /api/v1/sellers/{seller_id}`: Only the owner of the seller_id
  - `GET/PUT /api/v1/stores/{store_id}`: Only the owner of the store_id
  - `GET /api/v1/admin/`: Only administrators
  - `PUT /api/v1/orders/{order_id}/status`: Only admin or seller of the order

### Permission checking
- **Resource owner**: `user_id` from request == `resource.user_id`
- **Seller isolation**: `store.seller_id` == `request.seller_id` or `is_admin`
- **Admin override**: `is_admin` from request allows everything
- **Role-based**: `is_seller`, `is_moderator`, `is_admin` verified

## Password protection with Argon2

### Configuration
- **Algorithm**: argon2id (highest security level)
- **Hash**: Standard format: `$argon2id$v=19$m=65536,t=3,p=4$` + salt + hash
- **Salt**: Random per user, 16 bytes
- **Parameters**:
  - Memory: 64MB (65536 KB)
  - Iterations: 3
  - Parallelism: 4
  - Hash length: 32 bytes

### Code usage
```python
from argon2 import PasswordHasher

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)

# Hash
password_hash = ph.hash(password)

# Verify
ph.verify(password_hash, password)
ph.verify(password_hash, password, tolerate_milliseconds=50)
```

### Security
- **No plaintext storage**: Only hash
- **No salt reuse**: Generate random salt per user
- **Rate limit**: 5 attempts per user per hour for login
- **User enumeration**: No indication if email exists in registration
- **Hash strength**: Use high parameters to prevent GPU attacks
- **Slow verification**: Hash time ~100ms on server CPU

## JWT usage

### JWT configuration
- **Algorithm**: RS256 (asymmetric)
- **Issuer**: `plataforma-comercio-server`
- **Audience**: `plataforma-comercio-frontend`
- **Secret**: RSA-2048 private key, protected with environment variables
- **Expiry**: 15 minutes (access), 7 days (refresh)

### Token strategy
- **Access token**: Short-lived, content: `user_id, username, role, exp, iat`
- **Refresh token**: Long-lived, stored in database, random
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
- **Row-level security**: Each query filtered by appropriate seller_id
- **Row functions**: `is_seller_of_store(store_id)` returns bool
- **Policies**: RLS enabled, role-based restriction

### Authorization checks
- **Access control list**: Blacklist/white-list by seller_id
- **Materialized views**: `v_products_by_seller` filtered automatically
- **Debug mode**: No display of other sellers' data in logs

### Module isolation
- **seller-module**: Only data of the owning seller
- **store-module**: Only stores of the seller
- **product-module**: Only products of the seller's stores
- **order-module**: Only orders/sub-orders of the seller's products
- **commission-module**: Only commissions of the seller

### Security scenarios
- **Seller A** cannot view **Seller B**'s products or orders
- **Admin** can view everything (with audit restrictions)
- **Seller** can only modify their own data
- **Users** can only view products and create orders

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
- **Password hash**: Argon2, random salt
- **Payment data**: Tokenization in external payment services
- **Personal information**: Encryption in transit (HTTPS), encryption in rest (TLS)
- **Logs**: No logging of passwords, tokens, payment data

### Audit and monitoring
- **Failed access attempts**: Log failed login attempts
- **Sensitive data**: Mask in logs (e.g., email → us***@***.com)
- **Data changes**: Log changes in important tables (users, orders)
- **Monitoring**: Detection of anomalous patterns (e.g., multiple failed logins)

### TLS and HTTPS
- **All endpoints**: Only HTTPS in production
- **HSTS**: Implemented (max-age: 31536000)
- **Encryption**: TLS 1.2+, preferring forward-secure ciphers
- **Certificates**: Let's Encrypt or corporate certificate

## Personal data protection

### GDPR/LGPD compliance
- **Consent**: Obtain explicit consent for personal data
- **Data access**: Endpoints for users to access/delete their data
- **Portability**: Export data in machine-readable JSON format
- **Retention**: Retention policies for personal data (e.g., 1 year)
- **Deletion**: Delete data within 30 days after account deletion

### Consent flow
1. **Registration**: Marketing consent (separate checkbox)
2. **Cookies**: Cookie banner with granular acceptance
3. **Email**: Double opt-in for promotional emails
4. **Third-party data**: No sharing without explicit consent

### Data retention
- **Users**: Retain for 1 year after last activity
- **Orders**: Retain for 5 years (accounting)
- **Inventory**: Retain for 6 months
- **Reviews**: Retain for 3 years
- **Logs**: Retain for 30 days

## Database security

### PostgreSQL configuration
- **SSL**: TLS mandatory for connections
- **Authentication**: Strong passwords, principle of least privilege
- **Permissions**: Users with only necessary read/write permissions
- **Backups**: AES-256 encryption, stored in S3
- **Monitoring**: Change auditing, access attempt detection

### Access control
- **Least privilege**: Each user/module has minimum necessary permissions
- **Role-based**: Specific users for operations
- **Row-level**: RLS for filtering rows by seller_id

## Summary of security measures

1. **Authentication**: JWT + Refresh tokens + Argon2 password hash
2. **Authorization**: Role-based + row-level security + owner checks
3. **Input validation**: Pydantic + sanitization + SQL injection prevention
4. **Data protection**: HTTPS/TLS + encryption in transit + HTTPS only
5. **Access control**: JWT + seller isolation + admin override
6. **Rate limiting**: Global + login + register + password reset limits
7. **Audit trails**: Access logs + data changes + masked sensitive data
8. **Password security**: Argon2id + random salt + slow hashing
9. **Data retention**: Policies per regulations + secure deletion
10. **Compliance**: GDPR/LGPD + HTTPS + GDPR-compatible
