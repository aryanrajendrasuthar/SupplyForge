# SupplyForge

Enterprise-style supply chain and inventory management platform: supplier
lifecycle, product catalog, inventory tracking, order management, an async
data-ingestion pipeline with AI-assisted validation, and reporting —
built as independently deployable microservices behind a GraphQL gateway.

This is a from-scratch, IP-clean build of the *problem domain*: no
proprietary source, schemas, or data from any prior employer. See
[`docs/project-plan.md`](docs/project-plan.md) for the full scope and
rationale.

## Architecture

Six Flask services (each owning its own SQL Server data), an
`ai-validation-worker` consuming SQS events, a MongoDB-backed ingestion
store, an Ariadne GraphQL gateway, and a React/TypeScript dashboard.
See [`docs/architecture.md`](docs/architecture.md) for the full diagram and
the reasoning behind service boundaries, the order/inventory saga, and
async ingestion.

## Tech stack

| Layer | Stack |
|---|---|
| Services | Python 3.12, Flask, Pydantic |
| GraphQL gateway | Ariadne |
| Relational data | SQL Server (Docker locally, Azure SQL free tier for prod) |
| Document data | MongoDB (Docker locally, Atlas free tier for prod) |
| Messaging | ElasticMQ locally (SQS-API-compatible), AWS SQS free tier in prod |
| Async jobs | AWS Lambda free tier |
| Object storage | Cloudflare R2 |
| AI-assisted validation | Groq |
| Observability | Sentry + Grafana Cloud |
| Frontend | React + TypeScript, Vercel |
| CI/CD | GitHub Actions (`pip-audit`, TruffleHog, CodeQL, tests) |

## Repository layout

```
services/            Flask microservices, one directory each
gateway/graphql-gateway/  Ariadne GraphQL aggregation layer
frontend/dashboard/  React + TypeScript dashboard
shared/auth/         Shared Argon2id/TOTP/session package used by every service
infra/               docker-compose, Terraform, GitHub Actions definitions
docs/                Project plan, architecture, incident runbook
```

## Local development

Requirements: Docker, Python 3.12, Node 20+.

```bash
# start local infra (SQL Server, MongoDB, Redis, ElasticMQ)
docker compose -f infra/docker-compose.yml up -d

# run a service (example: catalog-service)
cd services/catalog-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app app run --debug
```

Each service has its own `README` section (in-code) covering its endpoints
and env vars. No external accounts are required for local dev — everything
runs in Docker. Production deploys wire real MongoDB Atlas / AWS / Groq /
Sentry credentials via `.env`, with no code changes.

## Security

See [`SECURITY.md`](SECURITY.md) for the full control set (auth, rate
limiting, IDOR checks, encryption, CI security gates) and how to report a
vulnerability.

## Status

Actively being built, phase by phase — see the Build Phases table in
[`docs/project-plan.md`](docs/project-plan.md#6-build-phases) for what's
shipped vs. in progress.

## License

Proprietary — All Rights Reserved. See [`LICENSE`](LICENSE). Source is
visible for portfolio/evaluation purposes; it is not licensed for reuse.
