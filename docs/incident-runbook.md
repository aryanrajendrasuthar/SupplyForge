# Incident Runbook

Blast-radius-first triage: establish what's actually affected before
guessing at root cause.

## 1. Triage order

1. **Scope the blast radius first.** Which service(s) are erroring? Check
   Sentry for the affected service, then pull the `X-Correlation-ID` off a
   failing request and search for it across every service's logs to see
   how far the failure propagated.
2. **Check the event bus before the database.** Most cross-service
   incidents in this architecture show up as a stuck or backed-up SQS
   queue (check `ai-validation-worker` and `inventory-service` consumer
   lag) before they show up as a database problem — services fail
   independently by design, so a single DB blip should not fan out.
3. **Check dead-letter queues.** A record that failed validation or
   processing three times lands in the DLQ, not silently disappears.
   Anything in a DLQ is an active incident, not a background task.
4. **Only then check the database/service the error points to.**

## 2. Common incident classes

| Symptom | Likely cause | First check |
|---|---|---|
| Orders stuck in `pending` | inventory-service not consuming `order.created` | SQS consumer health, inventory-service logs for the correlation ID |
| Ingested records never validated | ai-validation-worker down or Groq rate-limited | worker logs, DLQ depth, Groq API status |
| Stale prices on dashboard | `pricing.updated` event not published or not consumed | catalog-service publish logs, gateway cache subscriber logs |
| 401s across all services | shared `auth` package session validation issue (not a single-service bug) | shared/auth logs, Redis session store connectivity |

## 3. Rollback policy

- Each service deploys independently — roll back the one service that
  regressed, not the whole stack.
- Database migrations are additive-first (add column/table, backfill,
  switch reads, remove old column in a later release) specifically so a
  service rollback never requires a matching migration rollback.

## 4. Post-incident

- Every incident gets a short writeup: what broke, blast radius, root
  cause, the fix, and one concrete follow-up (a test, an alert, or a
  guardrail) that would have caught it sooner.
