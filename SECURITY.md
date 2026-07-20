# Security

No system is provably unbreakable, and this document doesn't claim
SupplyForge is. What it describes is defense-in-depth: no easy unauthorized
access, no known weak points, least-privilege by default, and failures that
fail safe and get logged rather than fail open silently.

## Reporting a vulnerability

This is a single-maintainer portfolio project. If you find a vulnerability,
open a private security advisory on the GitHub repo rather than a public
issue. There is no bug bounty.

## Controls in place

| Area | Control |
|---|---|
| Password storage | Argon2id, per-user salt (`shared/auth`) |
| Second factor | TOTP verification is implemented (`shared/auth`) and enforced at login if a user has a `totp_secret` set, but there's no enrollment endpoint yet to set one — a stated gap, not a silent one |
| Sessions | 256-bit random tokens (`secrets.token_urlsafe`) in Redis, HttpOnly + Secure + SameSite=Strict cookies, server-side revocation via `/auth/logout` |
| Rate limiting | 10 requests / 15 min on `supplier-service`'s `/auth/*` endpoints; Redis-backed limiter (200/hour default) on every other service, verified to return 429 under load |
| Authorization | Every mutation across catalog/inventory/order/supplier requires a valid session (`require_session()`); supplier approve/reject/deactivate additionally require the `approver` role. This is role-based, not per-resource-owner IDOR — there's no customer-account system yet under which "IDOR" (user A reading user B's private record) would apply; the closest analogue (an authenticated operator managing any supplier/order) is what's enforced |
| Input validation | Pydantic schema validation on every endpoint; parameterized queries only, no string-built SQL |
| Sensitive data at rest | Not implemented — no field currently collects tax IDs/banking info to encrypt. Flagged as a gap to revisit if/when that data is actually collected, rather than encrypting fields that don't exist |
| Network | Exact-origin CORS whitelist, no wildcard, in every environment including dev; verified with real preflight requests (`Access-Control-Allow-Origin` echoes the exact origin, `Allow-Credentials: true`) |
| Secrets | Zero hardcoded secrets; `.env` files are gitignored; production secrets come from a secrets manager |
| Dependency safety | `pip-audit` blocking CI merges |
| Secret scanning | TruffleHog blocking CI merges |
| Static analysis | Semgrep blocking CI merges |
| Error tracking | Sentry wired in from the first service commit (`sentry_sdk.init()`, guarded by `SENTRY_DSN`) — inert until a real DSN is configured, same stated tradeoff as Groq/AWS in `docs/project-plan.md` §1 |
| Compliance | Right-to-export (`GET /suppliers/:id/export`) and right-to-erase (`POST /suppliers/:id/erase`, PII scrubbed, audit trail kept) for supplier data. No equivalent yet for order/customer data — scoped to suppliers for now, not silently assumed to cover both |

## Reporting scope

In scope: any of the six services, the GraphQL gateway, the shared `auth`
package, or the frontend dashboard. Out of scope: third-party infrastructure
(GitHub, MongoDB Atlas, AWS, Vercel) — report those to the provider directly.
