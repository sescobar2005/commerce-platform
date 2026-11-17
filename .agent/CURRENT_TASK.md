# CURRENT_TASK.md

## Current Task Information

| Field | Value |
|-------|-------|
| Current phase | 1 (Fundamentals) |
| Current task | JWT token service (RS256) — COMPLETE |
| Objective | Implement reusable JWT token service using RS256 with RSA key pair from PEM files |
| Scope | `back/src/core/security/jwt.py`, `back/src/core/security/__init__.py`, `back/tests/test_jwt_unit.py`, `back/src/core/config.py`, `back/.env.example`, `back/.gitignore` |
| Files involved | `back/src/core/security/jwt.py`, `back/src/core/security/__init__.py`, `back/src/core/security/password.py`, `back/src/core/config.py`, `back/tests/test_jwt_unit.py`, `back/tests/test_password_unit.py`, `back/.env.example`, `back/.gitignore` |
| Completed units | Documentation baseline (6 docs), backend directory structure, config files, database engine configuration + connection pooling, unit tests, integration tests, SQLAlchemy session factory, session lifecycle/FastAPI dependency, session unit tests, session integration tests, Alembic configuration + env.py + unit tests, database models + unit tests, User model is_admin/is_moderator fields, Alembic initial migration + applied to PostgreSQL, password security service (Argon2id) + unit tests, JWT token service (RS256) + unit tests |
| Pending units | Authentication endpoints (registration/login) |
| Verification status | 17/17 JWT unit tests pass; 22/22 password unit tests pass; Python syntax verified for all files |
| Last updated | 2026-11-17 |

### Notes

JWT token service fully implemented:
- JWTService class with create_access_token(), create_refresh_token(), verify_access_token(), verify_refresh_token(), verify_token() methods
- RS256 asymmetric encryption using RSA private key for signing, public key for verification
- Keys loaded from PEM files via JWT_PRIVATE_KEY_PATH and JWT_PUBLIC_KEY_PATH environment variables
- JWT_ALGORITHM=RS256 enforced exclusively
- Token payload includes sub (user_id), username, role, iat, exp, type claims
- Access token expiry: 15 minutes; Refresh token expiry: 7 days
- Token type separation: access tokens rejected as refresh tokens and vice versa
- Malformed, expired, incorrectly signed tokens safely rejected
- No plaintext secrets in logs or code
- 17 unit tests: token generation, validation, expiration, signature verification, type separation, malformed tokens, invalid signatures, configuration errors
- .env.example updated with JWT_ALGORITHM, JWT_PRIVATE_KEY_PATH, JWT_PUBLIC_KEY_PATH
- JWT_SECRET_KEY removed from settings and .env.example
- .gitignore updated with *.pem, *.key, *.pub, *.asc patterns
