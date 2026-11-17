# CURRENT_TASK.md

## Current Task Information

| Field | Value |
|-------|-------|
| Current phase | 1 (Fundamentals) |
| Current task | Authentication dependencies (JWT validation) — COMPLETE |
| Objective | Implement reusable FastAPI authentication dependencies for JWT access token validation |
| Scope | `back/src/core/auth/dependencies.py`, `back/src/core/auth/__init__.py`, `back/tests/test_auth_dependencies_unit.py` |
| Files involved | `back/src/core/auth/dependencies.py`, `back/src/core/auth/__init__.py`, `back/tests/test_auth_dependencies_unit.py` |
| Completed units | Documentation baseline (6 docs), backend directory structure, config files, database engine configuration + connection pooling, unit tests, integration tests, SQLAlchemy session factory, session lifecycle/FastAPI dependency, session unit tests, session integration tests, Alembic configuration + env.py + unit tests, database models + unit tests, User model is_admin/is_moderator fields, Alembic initial migration + applied to PostgreSQL, password security service (Argon2id) + unit tests, JWT token service (RS256) + unit tests, authentication Pydantic schemas + unit tests, registration endpoint + unit tests, login endpoint + unit tests, authentication dependencies (get_current_user) + unit tests |
| Pending units | Logout endpoint (`POST /api/v1/auth/logout`) |
| Verification status | 12/12 auth dependency unit tests pass; 73/73 total security/auth tests pass; Python syntax verified for all files |
| Last updated | 2026-11-17 |

### Notes

Authentication dependencies fully implemented:
- `get_current_user()` FastAPI dependency that extracts Bearer token from Authorization header
- Validates JWT access token using JWTService.verify_access_token()
- Accepts only access tokens (rejects refresh tokens with "Invalid token type")
- Retrieves authenticated user by `sub` claim from database
- Returns UserResponse (no password_hash exposure)
- Consistent 401 for: missing header, invalid Bearer format, invalid signature, expired token, refresh token as access, malformed JWT, missing subject claim, nonexistent user
- Database errors raise 500
- 12 unit tests covering all security scenarios
- No logout, no refresh endpoint, no token revocation, no new migrations
