# ARCHITECTURE.md

## System overview

**Plataforma de Comercio** is a multi-vendor e-commerce platform where multiple sellers administer their own stores and products, while buyers explore products, manage shopping carts, and place orders.

## Architecture

**Modular monolith**: The backend is organized as a monolith divided into modules with well-defined responsibilities. This balances monolith simplicity with modular maintainability.

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

The backend is divided into 13 modules:

| Module | Responsibilities |
|--------|-----------------|
| **auth-module** | User management (registration, login, logout), credential validation, JWT session control |
| **user-module** | Buyer and seller profiles, account configuration, user preferences |
| **seller-module** | Seller registration, store management, store authorization, payment data (simulated) |
| **store-module** | Store information, store configuration, image management |
| **category-module** | Product category definition, category hierarchy, label management |
| **product-module** | Product catalog, inventory management, pricing, images, stock control |
| **cart-module** | Temporary product management, price calculations, cross-device synchronization |
| **order-module** | Order creation and tracking, commission calculation, sub-orders by seller, backend price validation |
| **payment-module** | Simulated payment processing, commission calculation, refund control |
| **commission-module** | Commission calculation, seller payment tracking, financial reports |
| **review-module** | Product reviews, store reviews, content moderation |
| **notification-module** | Email alerts, in-app notifications, system alerts |
| **admin-module** | General statistics, system audit, user management, seller monitoring |

## Frontend and backend communication

- **REST API**: Traditional REST endpoints
- **HTTP/HTTPS**: Standard protocol for all calls
- **JSON**: Standard format for request/response payloads
- **JWT**: Token-based authentication in `Authorization` header
- **CORS**: Configured for cross-origin communication
- **Versioning**: API v1 via URL prefix (`/api/v1`); v2 TBD

## Multi-vendor strategy and data isolation

### Data isolation
- Each seller can only access their own data
- Stores are associated with a specific seller
- The system implements permission checks

### Multi-vendor order design
- **Main order**: Represents the complete buyer purchase
- **Sub-orders**: Each seller receives an independent sub-order
- **Backend calculation**: Sub-order amounts are calculated by the backend, never trusted from the client
- **Validation**: The backend validates all price calculations before order creation

### Order flow
1. Buyer adds products to cart from multiple sellers
2. Cart is validated in real time
3. At checkout, sub-order amounts are calculated per seller
4. Main order and sub-order records are created
5. Inventory is updated per product
6. Payments are simulated
7. Commissions are calculated and registered

### Accounting isolation
- Each seller maintains independent accounting (revenue, commissions)
- Payments to sellers are tracked per sub-order
- Seller statistics are isolated
- Admin panel views aggregated data

## Critical design points

- **Modular monolith**: Balance between simplicity and maintainability
- **Backend calculation**: Prevents fraud and ensures consistency
- **Data isolation**: Guarantees security and privacy between sellers
- **Payment simulation**: Reduces initial complexity; migration to real payments TBD
- **Sub-orders**: Maintain clear accounting per seller
- **Clear responsibilities**: Each module has a single responsibility

## Architecture diagram

```
Frontend (Next.js)  <-- HTTP/HTTPS -->  Backend (FastAPI)
                                            |
                                            v
                                      +-------------+
                                      | auth-module |
                                      | user-module |
                                      | seller-module |
                                      | store-module |
                                      | category-module |
                                      | product-module |
                                      | cart-module   |
                                      | order-module  |
                                      | payment-module|
                                      | commission-module |
                                      | review-module   |
                                      | notification-module |
                                      | admin-module    |
                                      +-------------+
                                            |
                                            v
                                      PostgreSQL (Alembic)
```

## Pending decisions (TBD)

- **API v2 migration**: Timing and breaking changes TBD
- **Caching strategy**: What to cache (carts, products, etc.) TBD
- **Messaging setup**: Notification system transport TBD
- **Monitoring principles**: Metrics and alerts definition TBD
