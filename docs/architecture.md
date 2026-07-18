# Architecture

## Overview

SupplyForge is a set of independently deployable Flask services, each owning
its own data, fronted by a GraphQL gateway and consumed by a single React
dashboard. Services never call each other's databases directly — they talk
through REST (synchronous) or SQS events (asynchronous), and the gateway is
the only place cross-service data gets aggregated.

```
                         ┌─────────────────────┐
                         │   React Dashboard    │
                         └──────────┬───────────┘
                                    │ GraphQL
                         ┌──────────▼───────────┐
                         │   GraphQL Gateway     │  (Ariadne, resolver-level auth)
                         └───┬────┬────┬────┬────┘
              REST/gRPC calls│    │    │    │
          ┌───────────────────┘    │    │    └───────────────────┐
          │                        │    │                        │
┌─────────▼────────┐   ┌───────────▼──┐ ┌▼─────────────┐  ┌───────▼──────┐
│ supplier-service  │   │catalog-service│ │inventory-svc │  │ order-service│
│  (SQL Server)     │   │ (SQL Server)  │ │(SQL Server)  │  │(SQL Server)  │
└────────────────────┘  └───────────────┘ └──────┬───────┘  └──────┬───────┘
                                                   │  SQS events    │
                                          ┌────────▼────────────────▼──────┐
                                          │        Event Bus (SQS)         │
                                          └────────┬────────────────────────┘
                                                   │
                                     ┌─────────────▼──────────────┐
                                     │      ingestion-service      │──▶ MongoDB (raw payloads)
                                     └─────────────┬────────────────┘
                                                   │ SQS
                                     ┌─────────────▼──────────────┐
                                     │   ai-validation-worker      │──▶ Groq API (async anomaly pass)
                                     └──────────────────────────────┘
```

## Why services don't share a database

Each service owns its schema. Cross-service reads happen through the
GraphQL gateway (synchronous, request-time aggregation) or through SQS events
(asynchronous, eventual consistency) — never through a shared connection
string. This is what lets each service be developed, tested, and deployed
independently, and it's a deliberate correction of the tight coupling problem
called out as a weakness in the source domain.

## Order/Inventory Saga

Order creation is a two-step saga, not a single distributed transaction:

1. `order-service` creates the order in a `pending` state and publishes
   `order.created` to SQS.
2. `inventory-service` consumes the event, attempts to reserve stock, and
   publishes either `inventory.reserved` or `inventory.reservation_failed`.
3. `order-service` consumes the reservation result and transitions the order
   to `confirmed` or `cancelled`.

If any step fails, the compensating action is publishing the failure event —
there is no rollback across databases. Every event carries a correlation ID
so the full saga can be traced across services in logs/Sentry.

## Async ingestion + AI validation

Incoming records (file upload or REST push) are written to MongoDB and
acknowledged immediately — validation is **not** inline. A separate
`ai-validation-worker` consumes an SQS queue, runs the anomaly-detection pass
against Groq, and writes a validation verdict back onto the record. This is
the direct fix for the original system's known weakness: inline AI validation
adding latency to the ingestion path.

## Cache invalidation

Pricing data (read-heavy, in `catalog-service`) is cached, but invalidation is
event-driven: any mutation to a SKU's pricing publishes `pricing.updated`,
which cache-holding services subscribe to and evict on. No bare TTL-only
caching for pricing.

## Correlation IDs

Every inbound request generates (or forwards) an `X-Correlation-ID` header.
It propagates through every downstream REST call and SQS message attribute,
and is attached to every log line and Sentry event, so a single request can
be traced end-to-end across services.

## Local infra

`infra/docker-compose.yml` runs SQL Server, MongoDB, Redis, and ElasticMQ
(SQS-API-compatible) locally — no external accounts needed for development.
Production swaps connection strings to MongoDB Atlas, real AWS SQS/Lambda,
and Cloudflare R2 without any code changes (see `docs/project-plan.md` §1).
