# CURRENT_TASK.md

## Current Task Information

| Field | Value |
|-------|-------|
| Current phase | 1 (Fundamentals) |
| Current task | Authentication endpoints - Login endpoint — COMPLETE |
| Objective | Implement POST /api/v1/auth/login endpoint with JWT token issuance |
| Scope | `back/src/core/auth/router.py`, `back/tests/test_auth_login_unit.py` |
| Files involved | `back/src/core/auth/router.py`, `back/tests/test_auth_login_unit.py` |
| Completed units | Documentation baseline (6 docs), backend directory structure, config files, database engine configuration + connection pooling, unit tests, integration tests, SQLAlchemy session factory, session lifecycle/FastAPI dependency, session unit tests, session integration tests, Alembic configuration + env.py + unit tests, database models + unit tests, User model is_admin/is_moderator fields, Alembic initial migration + applied to PostgreSQL, password security service (Argon2id) + unit tests, JWT token service (RS256) + unit tests, authentication Pydantic schemas + unit tests, registration endpoint + unit tests, login endpoint + unit tests |
| Pending units | Logout endpoint |
| Verification status | 10/10 login unit tests pass; 73/73 total security/auth tests pass; Python syntax verified for all files |
| Last updated | 2026-11-17 |

### Notes

Login endpoint fully implemented:
- POST /api/v1/auth/login
- Accepts UserLoginRequest (username, password)
- Finds user by username
- Verifies password using PasswordService.verify_password() (Argon2id)
- Returns consistent 401 for unknown users AND incorrect passwords (no user enumeration)
- Generates access token using JWTService.create_access_token() with sub, username, role, iat, exp, type claims
- Generates refresh token using JWTService.create_refresh_token() with sub, iat, exp, type claims
- Returns UserLoginResponse (access_token, refresh_token, token_type, user)
- Updates last_login_at on successful login
- Persists update via SQLAlchemy session
- Handles IntegrityError with rollback and 500 INTERNAL_SERVER_ERROR
- 10 unit tests: successful login, incorrect password, unknown username, password verification called once, last_login_at update, db failure rollback, input validation (empty username/password, too long username/password)
- No JWT generation during registration (per task scope)
- No logout endpoint
