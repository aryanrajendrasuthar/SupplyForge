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
| Password storage | Argon2id, per-user salt |
| Second factor | TOTP-based 2FA |
| Sessions | 256-bit random tokens, HttpOnly + Secure + SameSite=Strict cookies, server-side revocation |
| Rate limiting | 10 requests / 15 min on auth endpoints; Redis-backed limiter on all other endpoints |
| Authorization | Server-side IDOR checks on every mutation (supplier records, orders, inventory adjustments) — resource ownership/role is never trusted from the client |
| Input validation | Pydantic schema validation on every endpoint; parameterized queries only, no string-built SQL |
| Sensitive data at rest | AES-256-GCM field-level encryption for tax IDs / banking info |
| Network | Exact-origin CORS whitelist, no wildcard, in every environment including dev |
| Secrets | Zero hardcoded secrets; `.env` files are gitignored; production secrets come from a secrets manager |
| Dependency safety | `pip-audit` blocking CI merges |
| Secret scanning | TruffleHog blocking CI merges |
| Static analysis | CodeQL/Semgrep blocking CI merges |
| Error tracking | Sentry wired in from the first service commit |
| Compliance | Right-to-delete and right-to-export endpoints for supplier/customer data; 30-day log retention |

## Reporting scope

In scope: any of the six services, the GraphQL gateway, the shared `auth`
package, or the frontend dashboard. Out of scope: third-party infrastructure
(GitHub, MongoDB Atlas, AWS, Vercel) — report those to the provider directly.
