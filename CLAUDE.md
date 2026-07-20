# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

SupplyForge is a multi-service supply chain/inventory platform: six Flask
services, a shared auth package, an Ariadne GraphQL gateway, and a React
dashboard. Full context lives in `docs/project-plan.md` (scope, tech stack,
security baseline, build phases) and `docs/architecture.md` (service
boundaries, saga flow, why services don't share databases). Read those
before making structural changes — don't re-derive decisions already made
there.

## Ground rules

- **No shared databases across services.** Each service owns its schema.
  Cross-service reads go through the GraphQL gateway; cross-service writes
  go through SQS events. Never add a direct DB connection from one service
  into another's database.
- **Auth/session logic lives in `shared/auth/`**, imported by every service
  that needs it via `-e ../../shared/auth` in `requirements.txt` (which is
  why those services' Dockerfiles build from repo-root context, not their
  own directory — see any of catalog/inventory/order/supplier-service's
  Dockerfile). Don't re-implement Argon2id hashing, TOTP, or session token
  generation inside an individual service.
- **Sessions are login-service-agnostic.** Only `supplier-service` has
  `/auth/register` and `/auth/login`, but the session itself is a JSON blob
  in Redis (`{user_id, email, role}`, see `SessionStore`) that every service
  resolves independently via `require_session()` — no service needs its own
  Users table or a call back to supplier-service to check who's logged in.
  When gating a new mutation, reach for `@require_session()` (or
  `@require_session(role="...")`) from `supplyforge_auth`, not a new
  ad-hoc check.
- **The GraphQL gateway forwards, never re-checks, auth.** It has no
  session logic of its own — `app/clients.py`'s `_forwarded_cookies()`
  relays the caller's cookie to whichever backend service it's proxying to,
  and that service's own `require_session()` is what actually enforces it.
  If a new resolver calls a gated backend endpoint, this happens
  automatically; don't add a parallel auth check in the resolver.
- **Every mutation needs a server-side authorization check** — session
  and/or role verified in the service layer (via `require_session()`),
  never trusted from a client-supplied field. (This is role-based, not
  classic per-resource-owner IDOR — there's no customer-account system
  under which that distinction would apply yet; see `SECURITY.md`.)
- **Every endpoint validates input with Pydantic schemas** in that
  service's `schemas/` directory, and uses parameterized queries only.
- **No hardcoded secrets.** Config comes from `.env` (gitignored); commit
  `.env.example` with variable names and dummy/placeholder values only.
- **Migrations are additive-first**: add column/table → backfill → switch
  reads → remove old column in a later change. This is what lets one
  service roll back without a matching DB rollback (see
  `docs/incident-runbook.md`).
- Correlation IDs (`X-Correlation-ID`) propagate through every REST call and
  SQS message attribute, and must appear in every log line touching a
  request.

## Code style

- Keep it minimal — no speculative abstractions, no config for hypothetical
  future requirements. Three similar lines beat a premature helper.
- No docstrings/comments explaining *what* code does; only comment
  non-obvious *why* (a workaround, a subtle invariant).
- Python: type hints throughout, Pydantic models for all request/response
  schemas, `black`/`ruff` formatting.
- TypeScript: strict mode on, no `any` without a comment explaining why it's
  unavoidable.

## Local dev

```bash
docker compose -f infra/docker-compose.yml up -d   # SQL Server, MongoDB, Redis, ElasticMQ
```

Each service is independently runnable — `cd services/<name>`, create a
venv, `pip install -r requirements.txt`, `cp .env.example .env`,
`flask --app app run --debug`. No external accounts needed for local dev;
production credentials (MongoDB Atlas, AWS, Groq, Sentry) are wired via
`.env` only, never committed.

## Testing

- Every service has a `tests/` directory using PyTest.
- Run a single service's tests: `cd services/<name> && pytest`.
- CI (`.github/workflows/ci.yml`) runs tests, `pip-audit`, TruffleHog, and
  static analysis on every PR — all blocking.

## Commit/PR conventions

- Commit messages: imperative mood, explain *why* not *what* the diff shows.
- Don't bundle unrelated services' changes into one commit unless it's a
  cross-cutting change (e.g. the shared `auth` package).
- Never commit `.env`, credentials, or `infra/terraform/*.tfstate`.

## Build phases

See `docs/project-plan.md` §6 for the authoritative phase list. Work
proceeds phase by phase — don't jump ahead to a later phase's service
before the current one has working tests and a green CI run.
