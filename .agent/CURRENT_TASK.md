# CURRENT_TASK.md

## Current Task Information

| Field | Value |
|-------|-------|
| Current phase | 1 (Fundamentals) |
| Current task | Authentication Pydantic schemas — COMPLETE |
| Objective | Implement reusable Pydantic schemas for authentication requests and responses |
| Scope | `back/src/core/security/schemas.py`, `back/tests/test_auth_schemas_unit.py` |
| Files involved | `back/src/core/security/schemas.py`, `back/tests/test_auth_schemas_unit.py` |
| Completed units | Documentation baseline (6 docs), backend directory structure, config files, database engine configuration + connection pooling, unit tests, integration tests, SQLAlchemy session factory, session lifecycle/FastAPI dependency, session unit tests, session integration tests, Alembic configuration + env.py + unit tests, database models + unit tests, User model is_admin/is_moderator fields, Alembic initial migration + applied to PostgreSQL, password security service (Argon2id) + unit tests, JWT token service (RS256) + unit tests, authentication Pydantic schemas + unit tests |
| Pending units | Authentication endpoints (registration/login) |
| Verification status | 19/19 schema unit tests pass; 58/58 total security/auth tests pass (22 password + 17 JWT + 19 schemas); Python syntax verified for all files |
| Last updated | 2026-11-17 |

### Notes

Authentication schemas fully implemented:
- `UserRegisterRequest`: username (str, 1-100), email (EmailStr, max 255), password (str, 1-255)
- `UserRegisterResponse`: user_id, username, email, is_seller, is_verified, created_at
- `UserLoginRequest`: username (str, 1-100), password (str, 1-255)
- `TokenResponse`: access_token, refresh_token, token_type (default "bearer")
- `UserLoginResponse`: access_token, refresh_token, token_type, user (UserResponse)
- `UserResponse`: user_id, username, email, is_seller, is_verified, created_at (no password_hash)
- 19 unit tests covering valid requests, missing fields, invalid email, field length validation, empty fields, response serialization, no password_hash exposure
- No JWT generation, no password hashing, no database operations, no endpoints
