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
- **Auth/session logic lives in `shared/auth/`**, imported by every service.
  Don't re-implement Argon2id hashing, TOTP, or session token generation
  inside an individual service.
- **Every mutation needs a server-side IDOR check** — resource
  ownership/role verified in the service layer, never trusted from a
  client-supplied ID alone.
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
