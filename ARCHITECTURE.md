# ARCHITECTURE.md

## System overview

**Plataforma de Comercio** is a multi-vendor e-commerce platform where multiple sellers can administer their own stores and products, while buyers can explore products, manage shopping carts, and place orders.

## chosen architecture

**Modular monolith**: The backend is organized as a carefully divided monolith into modules, each with well-defined responsibilities. This architecture balances the simplicity of a monolith with the maintainability of a modular architecture.

## Technologies and responsibilities

### Backend (Python 3.12+)
- **FastAPI**: REST API web framework
- **SQLAlchemy 2.0**: ORM for database interaction
- **Pydantic**: Validation and schema typing
- **Alembic**: Database migrations
- **PostgreSQL**: Relational database
- **JWT**: Token-based authentication
- **Argon2**: Secure password hashing
- **Pytest**: Testing suite
- **HTTPX**: HTTP client for external calls

### Frontend (Next.js)
- **Next.js**: SSR/RSC framework
- **TypeScript**: Static typing
- **Tailwind CSS**: Utility-first styling

## Modular backend organization

The backend is divided into the following modules:

### 1. auth-module (Authentication and Authorization)
- User management (registration, login, logout)
- Credential validation
- JWT session control

### 2. user-module (User profiles)
- Management of buyer and seller profiles
- Account configuration
- User preferences

### 3. seller-module (Seller management)
- Registration of new sellers
- Store management
- Store authorization
- Payment data (simulated)

### 4. store-module (Store management)
- Store information
- Store configuration
- Image management

### 5. category-module (Category catalog)
- Definition of product categories
- Category hierarchy
- Label management

### 6. product-module (Product catalog)
- Inventory management
- Product definition
- Images and specifications
- Stock control

### 7. cart-module (Shopping cart)
- Temporary product management
- Price calculations
- Cross-device synchronization

### 8. order-module (Order management)
- Order creation and tracking
- Commission calculation
- Sub-orders by seller
- Backend price validation

### 9. payment-module (Simulated payments)
- Simulated payment processing
- Commission calculation
- Refund control

### 10. commission-module (Commission system)
- Commission calculation
- Seller payment tracking
- Financial reports

### 11. review-module (Ratings and reviews)
- Product reviews
- Store reviews
- Content moderation

### 12. notification-module (Notifications)
- Email alerts
- In-app notifications
- System alerts

### 13. admin-module (Administration panel)
- General statistics
- System audit
- User management
- Seller monitoring

## Frontend and backend communication

- **REST API**: Traditional REST endpoints
- **HTTP**: Standard protocol for all calls
- **JSON**: Standard format for request/response payloads
- **JWT**: Token-based authentication in Authorization header
- **CORS**: Configured for cross-origin communication
- **Versioning**: API v1 (will be updated to v2 when needed)

## Multi-vendor strategy and data isolation

### Data isolation
- Each seller can only access their own data
- Stores are associated with a specific seller
- The system implements permission checks

### Multi-vendor order design
- **Main order**: Represents the complete buyer purchase
- **Sub-orders**: Each seller receives their own sub-order
- **Backend calculation**: Sub-order amounts are calculated by the backend, not sent by the client
- **Validation**: The backend validates all price calculations before order creation

### Order flow
1. The buyer adds products to cart from multiple sellers
2. The cart is validated in real time
3. At final purchase, sub-order amounts are calculated per seller
4. Main order and sub-order records are created
5. Inventory is updated per product
6. Payments are simulated
7. Commissions are calculated and registered

### Accounting isolation
- Each seller maintains their own accounting (revenue, commissions, etc.)
- The system tracks payments to sellers per sub-order
- Seller statistics are isolated
- The admin panel views aggregated data

## Critical design points

- **Modular monolith**: Balance between simplicity and maintainability
- **Backend calculation**: Prevents fraud and ensures consistency
- **Data isolation**: Guarantees security and privacy between sellers
- **Payment simulation**: Reduces initial complexity, allows future changes
- **Sub-orders**: Maintains clear accounting per seller
- **Clear responsibilities**: Each module has a single responsibility

## Architecture diagram

```
+------------------+     +------------------+
|     Frontend     |     |     Backend      |
|     (Next.js)    |     |     (FastAPI)    |
+------------------+     +------------------+
         |                       |
         |    HTTP/HTTPS          |
         |                       |
+------------------+     +------------------+
|   API Gateway    |     |   auth-module    |
+------------------+     +------------------+
         |                       |
         |   JWT Token           |
         v                       v
+------------------+     +------------------+
| Web/Mobile       |     |   user-module    |
|    Clients       |     +------------------+
+------------------+     |   seller-module  |
                        +------------------+
                        |   store-module   |
                        +------------------+
                        |   category-module|
                        +------------------+
                        |   product-module |
                        +------------------+
                        |   cart-module    |
                        +------------------+
                        |   order-module   |
                        +------------------+
                        |   payment-module |
                        +------------------+
                        |   commission-module|
                        +------------------+
                        |   review-module  |
                        +------------------+
                        |   notification-module|
                        +------------------+
                        |   admin-module   |
                        +------------------+
                               |
                               |
                           +-----------+
                           |           |
                           |   PostgreSQL
                           |  (Alembic)
                           +-----------+
```
