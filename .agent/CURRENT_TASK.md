# CURRENT_TASK.md

## Current Task Information

| Field | Value |
|-------|-------|
| Current phase | 1 (Fundamentals) |
| Current task | JWT Token Refresh Revocation Foundation — COMPLETE |
| Objective | Implement refresh token revocation foundation: jti claim, RevokedRefreshToken model, Alembic migration, revocation service, unit tests |
| Scope | `back/src/core/security/jwt.py`, `back/src/core/security/token_revocation.py`, `back/src/core/security/__init__.py`, `back/src/core/config.py`, `back/src/core/models/revoked_refresh_token.py`, `back/src/core/models/__init__.py`, `back/alembic/env.py`, `back/alembic.ini`, `back/alembic/versions/b67c867d7c26_add_revoked_refresh_tokens_table.py`, `back/tests/test_token_revocation_unit.py` |
| Files involved | `back/src/core/security/jwt.py`, `back/src/core/security/token_revocation.py`, `back/src/core/security/__init__.py`, `back/src/core/config.py`, `back/src/core/models/revoked_refresh_token.py`, `back/src/core/models/__init__.py`, `back/alembic/env.py`, `back/alembic/versions/b67c867d7c26_add_revoked_refresh_tokens_table.py`, `back/tests/test_token_revocation_unit.py` |
| Completed units | Documentation baseline (6 docs), backend directory structure, config files, database engine configuration + connection pooling, unit tests, integration tests, SQLAlchemy session factory, session lifecycle/FastAPI dependency, session unit tests, session integration tests, Alembic configuration + env.py + unit tests, database models + unit tests, User model is_admin/is_moderator fields, Alembic initial migration + applied to PostgreSQL, password security service (Argon2id) + unit tests, JWT token service (RS256) + unit tests, authentication Pydantic schemas + unit tests, registration endpoint + unit tests, login endpoint + unit tests, authentication dependencies (get_current_user) + unit tests, JWT refresh token jti claim, RevokedRefreshToken model, Alembic migration for revoked_refresh_tokens, token revocation service + unit tests |
| Pending units | Refresh token endpoint (`POST /api/v1/auth/refresh`), Logout endpoint (`POST /api/v1/auth/logout`) |
| Verification status | 11/11 token revocation unit tests pass; 122/122 total security/auth tests pass (pre-existing 28 failures unrelated); Python syntax verified for all files |
| Last updated | 2026-11-17 |

### Notes

Refresh token revocation foundation fully implemented:
- `create_refresh_token()` now includes `jti` claim (UUID4 string)
- `RevokedRefreshToken` model: jti (PK), user_id (FK→users, CASCADE), revoked_at, expires_at
- Alembic migration `b67c867d7c26` creates revoked_refresh_tokens table with proper indexes
- `TokenRevocationService` with `revoke_refresh_token()` and `is_token_revoked()` methods
- Idempotent revocation (revoking already-revoked token is no-op)
- Concurrent request safety (IntegrityError handling)
- 11 unit tests covering: revocation, idempotency, lookup, invalid signature, expired token, access token rejection, missing jti, missing user_id, missing expiration, database error rollback
- JWT_SECRET_KEY removed, JWT_ALGORITHM=RS256, JWT_PRIVATE_KEY_PATH/JWT_PUBLIC_KEY_PATH configured
- .gitignore updated with *.pem, *.key, *.pub, *.asc patterns
