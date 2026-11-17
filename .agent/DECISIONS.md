# DECISIONS.md

## Approved Technical Decisions

| Decision ID | Subject | Approved Decision | Reason | Date | Status |
|-------------|---------|-------------------|--------|------|--------|
| ARCH-001 | Backend architecture | Modular monolith | Balances monolith simplicity with modular maintainability | 2026-11-16 | Approved |
| ARCH-002 | Backend tech stack | Python 3.12+, FastAPI, SQLAlchemy 2.0, PostgreSQL | Specified in project requirements | 2026-11-16 | Approved |
| ARCH-003 | Frontend tech stack | Next.js, TypeScript, Tailwind CSS | To be developed by another team | 2026-11-16 | Approved |
| SEC-001 | Authentication | JWT with RS256 | Specified security requirement | 2026-11-16 | Approved |
| SEC-002 | Password hashing | Argon2id (64MB memory, 3 iterations, 4 parallelism) | High security level for password protection | 2026-11-16 | Approved |
| SEC-003 | Data isolation | Each seller can only access their own data | Multi-vendor requirement | 2026-11-16 | Approved |
| SEC-004 | User roles | user (buyer), seller (vendor), admin, moderator | Defined role-based access control | 2026-11-16 | Approved |
| ARCH-004 | Order design | Main order + independent sub-orders per seller | Multi-vendor accounting isolation | 2026-11-16 | Approved |
| ARCH-005 | Price calculation | Backend validates all price calculations; never trust client | Prevents fraud and ensures consistency | 2026-11-16 | Approved |
| ARCH-006 | Payment model | Simulated initially; migration to real payments TBD | Reduces initial complexity | 2026-11-16 | Approved |
| ARCH-007 | API versioning | API v1 via URL prefix (`/api/v1`); v2 TBD | Standard REST practice | 2026-11-16 | Approved |
| SEC-005 | JWT key management | RSA key pair from PEM files via JWT_PRIVATE_KEY_PATH and JWT_PUBLIC_KEY_PATH environment variables; JWT_SECRET_KEY removed | Asymmetric RS256 signing requires key pair; private key never committed | 2026-11-17 | Approved |

## Unresolved Questions / Pending Decisions

| ID | Subject | Status | Reference |
|----|---------|--------|-----------|
| TBD-001 | CI/CD pipeline tools and configuration | Pending | `DEVELOPMENT_PLAN.md` |
| TBD-002 | Database indexes, triggers, constraints | Pending | `DATABASE.md` |
| TBD-003 | API v2 migration timing | Pending | `ARCHITECTURE.md` |
| TBD-004 | Caching strategy (what to cache) | Pending | `ARCHITECTURE.md` |
| TBD-005 | Messaging/notification transport | Pending | `ARCHITECTURE.md` |
| TBD-006 | Monitoring metrics and alerts | Pending | `ARCHITECTURE.md` |
| TBD-007 | Refresh token storage (Redis vs database) | Pending | `SECURITY.md` |
| TBD-008 | Rate limit exact values per endpoint | Pending | `SECURITY.md` |
| TBD-009 | File upload storage (S3 vs alternative) | Pending | `API_SPECIFICATION.md` |
| TBD-010 | Certificate provider (Let's Encrypt vs corporate) | Pending | `SECURITY.md` |

> These decisions are summarized here for quick reference. The authoritative source for each decision is the corresponding root documentation file (`ARCHITECTURE.md`, `DATABASE.md`, `API_SPECIFICATION.md`, `SECURITY.md`, `DEVELOPMENT_PLAN.md`, `PROGRESS.md`).
