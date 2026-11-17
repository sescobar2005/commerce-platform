# CURRENT_TASK.md

## Current Task Information

| Field | Value |
|-------|-------|
| Current phase | 1 (Fundamentals) |
| Current task | Database models — COMPLETE |
| Objective | Define SQLAlchemy declarative models for core entities (users, sellers, stores, categories, products) |
| Scope | `back/src/core/models/` — User, Seller, Store, Category, Product models with relationships |
| Files involved | `back/src/core/models/__init__.py`, `back/src/core/models/user.py`, `back/src/core/models/seller.py`, `back/src/core/models/store.py`, `back/src/core/models/category.py`, `back/src/core/models/product.py`, `back/tests/test_models_unit.py` |
| Completed units | Documentation baseline (6 docs), backend directory structure, config files, database engine configuration + connection pooling, unit tests, integration tests, SQLAlchemy session factory, session lifecycle/FastAPI dependency, session unit tests, session integration tests, Alembic configuration + env.py + unit tests, database models (users, sellers, stores, categories, products) + unit tests, User model is_admin/is_moderator fields |
| Pending units | Alembic initial migration, authentication module |
| Verification status | Python syntax verified for all files; import/runtime tests not possible (dependencies not installed) |
| Last updated | 2026-11-16 |

### Notes

Database models fully implemented:
- User model: user_id (PK), username, email, password_hash, is_seller, is_verified, is_admin, is_moderator, created_at, last_login_at, preferences_json; 1:1 relationship with Seller
- Seller model: seller_id (PK, FK→users), store_name, business_name, tax_id, payment_info_json, bank_account, is_verified, created_at, last_login_at; 1:1 with User, 1:many with Store
- Store model: store_id (PK), seller_id (FK), name, description, slug, logo_url, cover_image_url, is_active, created_at, updated_at; many:1 with Seller, 1:many with Product
- Category model: category_id (PK), name, description, slug, parent_id (self-FK), level, path, is_active, created_at; self-referential hierarchy, 1:many with Product
- Product model: product_id (PK), store_id (FK), category_id (FK), name, description, price, cost, sku, stock, is_active, images_urls, created_at, updated_at; many:1 with Store and Category
- All models use SQLAlchemy 2.0 Mapped/mapped_column conventions
- All models inherit from Base (DeclarativeBase)
- Unit tests (test_models_unit.py): 16 tests covering model creation, defaults, repr, metadata registration, in-memory table creation
- No business tables beyond core models, no migrations created yet (per task scope)
