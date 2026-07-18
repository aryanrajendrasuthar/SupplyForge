# Project Plan — SupplyForge
**Enterprise Supply Chain & Inventory Management Platform**
(Real, portfolio-owned rebuild of the system domain described in the Avnet interview-prep documentation)

> Working name: **SupplyForge**. Renaming is a find-and-replace away — swap it before `claude-power` initializes the repo if you want something else.

---

## 0. Why this project exists

This isn't a toy CRUD app — it's a from-scratch, IP-clean rebuild of the *domain* you worked in at Avnet (supplier lifecycle, catalog, inventory, order management, high-volume ingestion), built by you, owned entirely by you, with no proprietary Avnet code, data, or internal names anywhere in it. It exists so that when you talk about this system in an interview, every line of code, every architectural decision, and every incident story is something you can open a laptop and show.

**Assumptions I'm making (override any of these before build):**
- No proprietary Avnet source, schemas, internal service names, or data formats are being reused — this is a clean-room rebuild of the *problem domain*, described in your own words in the interview doc.
- "Full feature set" means all six domains from Section 1.1 of the interview doc get real, working implementations — not stubs.
- Production-grade means real auth, real data validation, real observability — not a demo with hardcoded users.
- Single-developer team (you) — the plan is sequenced so each phase ships something runnable, not a big-bang integration at the end.

---

## 1. Tech Stack

Matched to the documented Avnet stack exactly. Where the documented choice has a paid managed-service on the natural growth path, a zero-cost substitute is named — same protocol/API, same code, swap the connection string later if you ever want the managed version.

| Layer | Exact-match stack | Zero-cost path (use this) | Notes |
|---|---|---|---|
| Backend services | Python 3.12, Flask | Same | No cost either way |
| GraphQL aggregation | Ariadne | Same | Free library |
| Relational DB | SQL Server | **SQL Server via Docker (Developer edition, free)** | Free forever for dev/non-prod; if you later need a hosted instance, Azure SQL free tier (32MB, fine for a portfolio project) or a self-managed VM |
| Document DB | MongoDB | **MongoDB Atlas free tier (M0, 512MB)** | Genuinely free, no card required initially |
| Messaging | AWS SQS | **AWS SQS free tier** (1M requests/month, permanently free) | If you blow past free tier: self-host ElasticMQ (SQS-API-compatible) in Docker, zero code changes |
| Serverless / validation jobs | AWS Lambda | **AWS Lambda free tier** (1M requests/month, permanently free) | Same reasoning as SQS |
| Object storage | AWS S3 | **Cloudflare R2 free tier** (10GB storage + free egress, S3-API-compatible) | S3's free tier expires after 12 months; R2's free tier doesn't, and the SDK calls are identical |
| Containerization | Docker | Same | Free |
| CI/CD | Jenkins | **GitHub Actions** (free for public repos, 2,000 min/mo free for private) | Self-hosting Jenkins costs you a server; GitHub Actions is the honest zero-cost swap and is what most interviewers expect to see anyway. Mention Jenkins knowledge in the README if you want that line on record. |
| Testing | PyTest | Same | Free |
| AI-assisted validation | (unspecified LLM) | **Groq free tier** | Matches your existing zero-cost stack pattern |
| Observability | Datadog (per interview doc) | **Sentry free tier** (errors) + **Grafana Cloud free tier** (metrics/dashboards) | Datadog has no meaningful free tier; this pairing covers the same ground |
| Frontend dashboard | (not specified in doc — needed for a demoable system) | **React + TypeScript, hosted free on Vercel** | Matches your core stack |
| Auth | — | Self-built per Security Baseline below | See §3 |

---

## 2. Feature Scope (full — matching all six domains)

1. **Supplier lifecycle** — registration, document upload, approval workflow (multi-step, with an approver role), deactivation, audit trail of status changes.
2. **Product catalog** — SKUs with attributes, images, technical specs, compliance certs, tiered pricing. Bulk import via file upload.
3. **Inventory tracking** — per-warehouse stock levels, reservation logic for in-flight orders, low-stock alerts.
4. **Order management** — PO creation, status tracking, fulfillment updates, shipping notifications, customer-facing order confirmation emails.
5. **Data ingestion pipeline** — CSV/JSON file upload + REST push endpoint, async processing via SQS, AI-assisted anomaly detection on incoming records (built as an **async post-processing pass**, not inline — this fixes the exact latency problem your interview doc flags as a known weakness in the original system).
6. **Reporting/analytics** — aggregated inventory + order data exposed via a reporting endpoint/dashboard for internal "analyst" use.

**Deliberately built in from day one** (things the interview doc calls out as gaps in the original, so building them correctly here is a stronger portfolio signal than replicating the gap):
- Async AI validation queue (not synchronous-in-pipeline)
- Eventual-consistency between order and inventory services via SQS events (not synchronous REST stock checks)
- Real GraphQL resolver integration tests spanning both databases
- Event-driven cache invalidation (not TTL-only) for pricing data

---

## 3. Security Baseline

Applied in full, adapted to this stack — nothing here is optional for a production-grade system:

- **Auth**: Argon2id password hashing, TOTP-based 2FA, session tokens as 256-bit random values in HttpOnly/Secure/SameSite=Strict cookies
- **Rate limiting**: 10 req/15min on auth endpoints; Redis-backed rate limiting on all other API endpoints
- **Authorization**: IDOR checks on every mutation (supplier records, orders, inventory adjustments) — resource ownership/role verified server-side, never trusted from the client
- **Input handling**: schema validation on every endpoint (marshmallow or pydantic, since this is Flask), parameterized queries only (no raw SQL string building), DOMPurify equivalent on any HTML the frontend renders from user input
- **Data**: AES-256-GCM field-level encryption for sensitive supplier data (tax IDs, banking info if collected); no RLS control here since SQL Server/MongoDB don't have Supabase-style RLS — enforce row-level access in the service layer instead
- **Network**: exact-origin CORS whitelist (no wildcard), even in dev
- **Observability**: Sentry wired in from the first commit, not bolted on later
- **CI gates**: `pip-audit` (dependency audit), TruffleHog (secret scanning), CodeQL or Semgrep (static analysis) — all blocking merges in GitHub Actions
- **Compliance basics**: right-to-delete/right-to-export endpoints for supplier and customer data, 30-day log retention policy, zero hardcoded secrets (`.env` + secrets manager, never committed)

## 4. License

**Recommendation: Proprietary — All Rights Reserved.**

This is production-grade, IP-owned work you may eventually productize or license — not a library meant for others to build on top of. Default to a rights-reserved notice rather than MIT. If you decide later you want it as an open portfolio showcase others can fork, switching to MIT is a one-line LICENSE file swap — flag that decision explicitly if you change your mind, don't do it silently.

---

## 5. Project Structure

```
supplyforge/
├── services/
│   ├── supplier-service/       # Flask — supplier lifecycle, approvals, audit trail
│   │   ├── app/
│   │   ├── tests/
│   │   └── Dockerfile
│   ├── catalog-service/        # Flask — SKUs, pricing, bulk import
│   ├── inventory-service/      # Flask — stock levels, reservations, low-stock alerts
│   ├── order-service/          # Flask — PO lifecycle, Saga orchestration with inventory
│   ├── ingestion-service/      # Flask — file/API intake, SQS producer
│   └── ai-validation-worker/   # SQS consumer — async anomaly detection pass
├── gateway/
│   └── graphql-gateway/        # Ariadne — aggregates all services, resolver-level auth
├── frontend/
│   └── dashboard/               # React + TypeScript — catalog/order/inventory UI, reporting views
├── infra/
│   ├── docker-compose.yml       # local: SQL Server, MongoDB, ElasticMQ, all services
│   ├── terraform/                # AWS resources (SQS, Lambda, R2) — free-tier sized
│   └── github-actions/           # CI: pip-audit, TruffleHog, CodeQL, tests, deploy
├── docs/
│   ├── project-plan.md          # this file, or project-planner's regenerated version
│   ├── architecture.md          # Saga flow, correlation-ID tracing, service boundaries
│   └── incident-runbook.md      # blast-radius-first triage process, from your own doc
├── SECURITY.md
└── LICENSE
```

**Where each security control lives:**
- Auth/session logic → shared `auth` package imported by every service (avoid re-implementing Argon2id/TOTP per service)
- Rate limiting → Redis instance in `docker-compose.yml`, middleware in each Flask app
- IDOR checks → service-layer, not resolver-layer, so GraphQL and any future REST clients both get it
- Schema validation → per-service `schemas/` directory (pydantic models)
- CI gates → `.github/workflows/ci.yml`, one workflow, all services

---

## 6. Build Phases

Sequenced so each phase ends with something runnable and demoable — not a big-bang integration.

| Phase | Deliverable |
|---|---|
| 0 — Infra bootstrap | `docker-compose.yml` with SQL Server, MongoDB, ElasticMQ running locally; empty service skeletons; CI pipeline green on "hello world" |
| 1 — Catalog + Inventory | Catalog CRUD + bulk import; inventory tracking with reservation logic; unit + integration tests |
| 2 — Supplier lifecycle | Registration, approval workflow, audit trail |
| 3 — Orders + Saga | Order creation, Saga-based inventory reservation/release, order status tracking |
| 4 — Ingestion + AI validation | File/API intake, SQS producer, async AI validation worker, dead-letter handling |
| 5 — GraphQL gateway + dashboard | Aggregation layer, resolver-level auth, React dashboard consuming it |
| 6 — Security + observability hardening | Full security baseline audit, Sentry/Grafana wired, correlation-ID tracing verified end-to-end |
| 7 — Deploy | Free-tier deploy (Fly.io/Render for services, Vercel for frontend), README + demo walkthrough for interviews |

---

## 7. How to hand this off to Claude Code

Unzip `claude-power-kit.zip`, run `./install.sh` once, then from an empty `supplyforge/` directory run:

```
claude-power
```

Upload this file alongside — the `project-planner` subagent will pick it up as grounding context for its own `docs/project-plan.md`, but you already have the license/security/structure decisions made here, so it shouldn't need to re-derive them from scratch. If it does regenerate `docs/project-plan.md`, diff it against this one before accepting — the intent here was to save it that guesswork.
