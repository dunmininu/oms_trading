# Enterprise OMS (IB) – Consolidated Architecture & Implementation Blueprint

> Author: Oluwaseyi Abiola-Alaka, Senior Software Engineer, Quant Trading
> Version: 1.0 • Date: 2025‑08‑10

---

## 0) Executive Summary

A production‑grade, multi‑tenant Order Management System (OMS) engineered around Interactive Brokers (TWS/Gateway) with a clear path to multi‑broker. This blueprint consolidates and elevates prior documents into a single enterprise standard covering architecture, security, operations, data design, APIs, and a milestone plan with acceptance criteria. It aligns with regulated trading environments (e.g., SEC/FINRA, FCA, MiFID II) and quant research needs.

**Primary outcomes**

* Low‑latency, resilient order routing with provable idempotency and full auditability.
* Deterministic risk/compliance gates (pre‑trade, in‑flight, post‑trade) with emergency halts.
* Real‑time market data, P\&L and positions; durable history with time‑series partitioning.
* API‑first platform (Django + Ninja) with RBAC/ABAC and strong tenant isolation.
* Operable at scale: SLOs, runbooks, observability, and disaster recovery.

---

## 1) Scope & Guardrails

**In scope:** IB connectivity (paper/live), order lifecycle, risk/compliance, positions/P\&L, market data, webhooks, strategy framework and sandbox, multi‑tenant RBAC, audit, CI/CD, K8s deployment, incident and DR runbooks.

**Out of scope (Phase‑2+):** Full backtesting engine, ML alpha platform, FIX gateway, mobile apps, multi‑region active‑active.

**Assumptions:**

* Single primary region; multi‑AZ PostgreSQL HA with PITR; Redis HA.
* Accurate time sync via NTP/PTP; all timestamps in UTC with tenant TZ presentation.
* IB paper/live accounts available; regulatory reporting requirements known per tenant.

---

## 2) Reference Architecture

### 2.1 System Context

* **Clients:** Web dashboard, CLI, programmatic API clients.
* **Gateway:** Nginx (WAF + TLS), Django + Ninja API.
* **Core Services:** AuthN/Z & Tenancy, OMS Core, Risk, Compliance, Market Data, Strategy Runner, Event Bus/Webhooks.
* **Broker Layer:** IB Connector (ib\_insync), IB Simulator, State Sync/Reconciliation.
* **Data Layer:** Postgres (OLTP), Redis (cache/queues), S3‑compatible storage.
* **Async:** Celery workers & Beat; Flower for monitoring.
* **Observability:** Structured logs, Prometheus, OpenTelemetry tracing, Sentry, health endpoints.

### 2.2 Latency Budgets (95p)

* API non‑broker: **< 150 ms**.
* Place order (client → broker ack): **< 500 ms**.
* Market tick broker → cache fan‑out: **< 100 ms**.

### 2.3 Availability Targets

* Market hours: **99.9%** service availability; RTO **15 min**, RPO **< 1 min** for OLTP; zero data loss for orders/executions via write‑ahead durability and reconciliation.

---

## 3) Domain & Data Design

### 3.1 Canonical Entities (consolidated & normalized)

* **Tenant, User, Membership**: *Single custom user model in `core.User`*; all FKs use `'core.User'` string refs. (Model cleanup applied.)
* **Broker, BrokerAccount**: Credential envelope encrypted; status, capabilities.
* **Instrument**: Symbol, exchange, type, currency, tick/min size; IB contract metadata json.
* **Order**: Client/Broker IDs, type, side, TIF, qty, price/stop/trail, state, reject reason, idempotency hash, metadata.
* **Execution**: Price, qty, commission, currency, exec time, metadata.
* **Position**: Qty, avg cost, realized/unrealized P\&L, last update.
* **PnL Snapshot**: Daily aggregates; denormalized positions snapshot for end‑of‑day reports.
* **RiskLimit**: Limit type (gross notional, per‑symbol qty, drawdown, order rate, exposure by asset class), scope (tenant/account/instrument), period, value.
* **ComplianceRule**: Wash trade detection, restricted hours/calendar, restricted symbols, throttling.
* **IdempotencyKey**: Endpoint, method, request hash, response, TTL.
* **AuditLog**: Actor, action, resources, before/after, IP/UA.
* **WebhookOut/Delivery**: Endpoint, secret hash, retries, DLQ.
* **MarketSubscription, TickData**: Subscriptions and ticks; persisted snapshots.
* **Strategy, StrategyRun**: Code ref/version, params, runtime config, metrics, logs path.

### 3.2 Data Modeling Standards

* **Keys:** UUID v4 PKs; natural keys where applicable (symbol, client\_order\_id with tenant).
* **Partitioning:**

  * `Execution`, `TickData`, `AuditLog`, `WebhookDelivery` → **time‑partitioned** (daily/weekly) using native partitioning or TimescaleDB.
  * `Order` → index on `(tenant_id, created_at desc)`, `(tenant_id, client_order_id)`, `(broker_order_id)`.
* **Indexes:** Composite indexes per query path (filters on tenant, state, instrument, created\_at). GIN for JSONB fields with strict schema subset.
* **RLS (Phase‑2):** PostgreSQL Row‑Level Security for tenant isolation, enforced via DB role.
* **Data Quality:** NOT NULL on mandatory fields; check constraints (e.g., `price > 0` for LIMIT orders; `quantity > 0`).

### 3.3 Ticks & Time‑Series

* **Hot path:** Redis pub/sub for fan‑out and last‑price cache.
* **Cold path:** Batched inserts every N ms; compression; retention policy (e.g., raw ticks 30 days, OHLCV 2 years.)

---

## 4) Order Lifecycle & State Machines

**States:** `NEW → ROUTED → PARTIALLY_FILLED → FILLED | REJECTED | CANCELED | EXPIRED`. (Add `PENDING_CANCEL`, `PENDING_MODIFY` for async broker acks.)

**Transitions guarded by:**

* **Idempotency:** SHA‑256 of (tenant, endpoint, payload canonicalized); dedupe window 24h (configurable).
* **Risk gates (pre‑trade):** symbol whitelist, order size/notional, position limit, per‑interval throttle, strategy envelope.
* **Compliance gates:** restricted hours/holidays, restricted symbols/accounts, wash trade checks.
* **Broker acks:** Map IB orderStatus to internal states; reconcile fills/executions.

**Cancellation/Modification:** Validation on state and remaining qty; optimistic concurrency via `version` column (ETag pattern).

**Reconciliation:** On reconnect, fetch open orders, executions (T‑1), and positions; 3‑way diff (local vs IB vs derived positions). Emit `OrderStateSync` events for any drift.

---

## 5) Broker Integration (Interactive Brokers)

### 5.1 Connector

* **Library:** `ib_insync` (async) wrapped in `libs/ibsdk` for unified interfaces.
* **Resilience:** Auto‑reconnect with exponential backoff + jitter; circuit breaker (half‑open probes). Heartbeats.
* **Contracts & Orders:** Mapping layer (OMS ↔ IB) with strict validation (e.g., TIF, good‑after‑time, outside RTH flags).
* **IB Gateways:** Separate pods for paper/live; readiness gated on session login. Optional VNC for ops only.

### 5.2 Supported Order Types (Phase‑1)

* Market (MKT), Limit (LMT), Stop (STP), Stop‑Limit (STP\_LMT), Trail (TRAIL), Market‑on‑Close (MOC), Limit‑on‑Close (LOC). TIF: DAY, GTC, IOC, FOK, GTD.

### 5.3 State Sync

* Fetch `openOrders`, `executionsSince`, `positions` after reconnect; reconcile per §4. Persist last sync cursor (ts, execId).

### 5.4 Observability

* Per‑account/broker SLI: connect time, disconnects/hour, submit latency, ack latency, reject rate, recon duration.

---

## 6) Risk & Compliance

### 6.1 Pre‑Trade Risk Engine

* **Static limits:** max order qty/notional, per‑symbol and per‑asset‑class caps, max leverage.
* **Dynamic limits:** open orders count, order rate (QPS) per user/strategy/account, daily loss limit, trailing drawdown.
* **Position checks:** resulting position exposure, concentration.
* **FX sanity:** Ensure currency alignment or auto‑FX (Phase‑2).

### 6.2 In‑Flight & Post‑Trade

* **In‑flight:** monitor partial fills vs residual limits; auto‑cancel if breach.
* **Post‑trade:** realized P\&L roll‑ups; commission normalization; end‑of‑day compliance snapshots.

### 6.3 Emergency Controls

* **Kill‑Switch:** Tenant/account/strategy level, idempotent, with audit and optional reason code.
* **Circuit Breakers:** Trigger on thresholds (loss, reject storm, latency spikes). Automated plus manual override.

### 6.4 Compliance

* Calendars for market holidays and RTH; restricted lists (symbols, venues); wash trade heuristics; full audit trail with WORM storage export.

---

## 7) API Surface (Ninja)

### 7.1 Global Conventions

* **Auth:** JWT (15 min) + refresh (7 days) OR scoped API keys. MFA optional.
* **Idempotency:** `Idempotency-Key` header for POST order‑creating endpoints; duplicate returns original 200/201.
* **Versioning:** URL `/api/v1/...`; deprecations via Sunset headers.
* **Pagination:** Cursor‑based (opaque `next`); server‑imposed max page.
* **Filtering/Sorting:** Whitelist per resource; sparse fieldsets via `fields=`.
* **Errors:** Structured envelope `{trace_id, code, message, details, hint}`.
* **SSE/WebSocket:** `/marketdata/stream` and `/events/stream` (Phase‑2 WebSocket).

### 7.2 Key Endpoints (consolidated)

* **Auth:** register, login, refresh, logout, rotate‑api‑key, profile CRUD.
* **Tenants:** CRUD, invite, members, roles.
* **Brokers (IB):** connect/status/disconnect, accounts.
* **Market Data:** instruments lookup, subscribe/unsubscribe, list subs, last price, stream.
* **Orders:** place/list/get/modify/cancel, executions. Bulk: `/orders/batch` (submit/cancel up to N=100 per request).
* **Positions & PnL:** positions (all/by symbol), PnL today/history, executions list.
* **Strategies:** CRUD, start/stop, runs, logs download.
* **Risk:** list/create/update/delete limits, status, override (audited).
* **Webhooks:** manage outbound endpoints, deliveries, incoming receiver.
* **System:** health/live/ready, metrics, version.

---

## 8) Security Architecture

### 8.1 Identity, AuthN/Z

* **User model:** single authoritative `core.User` (cleaned up). MFA (TOTP). Password policy and lockouts.
* **RBAC/ABAC:** Roles (Admin, Manager, Trader, Viewer) + scoped permissions; per‑token scopes.
* **Tenant Isolation:** App‑level scoping and DB schemas prepared for RLS (Phase‑2) with DB roles.

### 8.2 Data Protection

* **Transit:** TLS 1.3 only; HSTS; modern ciphers.
* **At rest:** AES‑256 for secrets & credentials; envelope encryption (KMS or Vault transit).
* **Secrets:** External store (HashiCorp Vault/AWS Secrets Manager); automatic rotation for API keys and IB creds.
* **Logging:** PII masking; never log secrets; tamper‑evident audit logs (hash chain) with optional WORM export to S3.

### 8.3 Network & Platform

* **Ingress WAF:** rate‑limit, bot protection, IP allowlists per tenant (optional).
* **K8s:** PodSecurity, NetworkPolicies, read‑only root FS for stateless pods; seccomp; non‑root users.
* **Supply Chain:** SBOM (CycloneDX), SAST/DAST in CI, image signing & admission policy.

### 8.4 Compliance Controls

* Data retention & deletion policy; subject access requests; configurable retention windows per tenant.
* Runbooks for incident response and regulator notifications.

---

## 9) Observability & Operations

### 9.1 SLIs & SLOs

* **Order submit latency** p95 < 500 ms; **reject rate** < 0.5% excluding broker rejects; **uptime** 99.9% market hours; **reconnect time** p95 < 60 s.

### 9.2 Telemetry

* **Metrics:** Business (orders/min, fills/min, P\&L by account), system (CPU, mem, GC, queue depth), broker (connectivity, acks).
* **Tracing:** OpenTelemetry across API → OMS → ibsdk; trace IDs returned to clients.
* **Logs:** JSON with correlation IDs; central aggregation (ELK/Vector + OpenSearch). Redaction filters.

### 9.3 Alerting

* PagerDuty/On‑call; severity matrix; quiet hours exceptions for market hours; synthetic checks (place paper order hourly).

### 9.4 Runbooks (excerpts)

* **IB Gateway down:** Fail to secondary gateway; force reconnect; reconcile; broadcast service notice.
* **Reject storm:** Trip circuit breaker; freeze strategies; inspect last deploy; rollback if needed.
* **DB failover:** Promote replica; rotate writers via proxy (pgBouncer/Patroni); verify replication; warm caches.

---

## 10) Deployment Architecture

### 10.1 Containers & Processes

* Web (Gunicorn + Django/Ninja); Celery workers by queue: `orders`, `marketdata`, `strategies`, `webhooks`, `reconcile`.
* Celery Beat; Flower (restricted & authenticated).
* IB Gateway pods (paper/live) with autosupervised login.

### 10.2 Kubernetes

* HPA by CPU and queue depth; PodDisruptionBudgets; anti‑affinity across AZs.
* Blue/Green or Canary via progressive delivery (Argo Rollouts).
* Config via env + ConfigMaps/Secrets; immutable images; zero‑downtime migrations with `safe_migrate` job.

### 10.3 Data Stores

* **Postgres:** primary + sync replica; PITR; pgBouncer; tuned autovacuum; logical decoding for audits (optional).
* **Redis:** HA (Redis Sentinel/Elasticache); key TTLs; memory policies.
* **S3:** logs, strategy artifacts, exports; lifecycle rules (retention tiers).

---

## 11) Strategy Framework

* **Base interface:** lifecycle hooks (`on_start`, `on_tick`, `on_bar`, `on_fill`, `on_stop`); async safe.
* **Execution:** Isolated per run with resource quotas; optional Docker sandbox; file system jailed; network egress policy.
* **Parameters:** Typed, validated, versioned; change history.
* **Paper trading:** Plug replacements for broker; determinism for replay.
* **Examples:** Echo, VWAP; reference templates with smart comments.

---

## 12) Eventing & Webhooks

* **Event bus:** internal topic names (order.created, order.routed, order.filled, order.rejected, order.canceled, risk.breached, broker.disconnected, broker.reconnected, position.updated, pnl.snapshot.created).
* **Delivery:** At‑least‑once with exponential backoff; signed payload (HMAC‑SHA256) + timestamp; `Replay‑Prevention` nonce; DLQ table.
* **Inbound:** Receiver for external events (phase‑2: FIX drop copy, compliance feeds).

---

## 13) API Error & Idempotency Contracts

* **Error envelope:** `code` (machine), `message` (human), `trace_id`, `details` (field errors), `hint`.
* **Idempotency:** store hash + response for 24h; only for POST that creates side‑effects; safe replays return 200/201 with original body.

---

## 14) Security Hardening Checklist (Enterprise)

* TLS 1.3, HSTS, CSP, secure cookies, CSRF where relevant, OAuth device‑flow off.
* Password policy, MFA, account lockout/ unlock flow, session revocation APIs.
* Vault‑backed secrets, periodic rotation; break‑glass accounts with monitoring.
* K8s PodSecurity, NetworkPolicies, image signing, read‑only FS, non‑root.
* SBOM, SAST (ruff/mypy + bandit), dependency scans, container CVE scans.
* Data classification & masking, right‑to‑erasure workflows.
* Immutable audit logs with hash chain and periodic notarization (optional).

---

## 15) Testing & Quality Strategy

* **Unit:** models, services, risk rules, mappings (≥80% coverage).
* **Contract tests:** Ninja schemas vs OpenAPI; schema drift guard.
* **Integration:** IB simulator end‑to‑end; order place/modify/cancel; reconnect & reconcile.
* **Load:** orders/min, ticks/sec; soak tests during market hours.
* **Chaos:** broker disconnects, DB failover, Redis eviction, latency injection.
* **Security:** authZ bypass attempts, rate‑limit, SSRF/file upload, secrets redaction.

---

## 16) Gap Analysis & Remediations (from current state)

**Already addressed**

* Single authoritative `core.User` model; settings & FKs updated accordingly.
* Solid project structure, Docker, Makefile, dev tooling.

**High‑impact gaps** (priority order)

1. **Auth/API layer** (JWT/API key, RBAC scopes, rate limiting, IP allowlists).
2. **IB connector service** (reconnect, mapping, state sync), plus health checks.
3. **Order services & API** (idempotent create/modify/cancel, state machine, audit).
4. **Market data** (subscriptions, Redis cache, streaming, snapshots, retention).
5. **Risk engine** (rule registry, pre‑trade gates, throttles, circuit breakers).
6. **Event bus & webhooks** (HMAC, retries, DLQ, deliveries UI).
7. **Observability** (metrics, tracing, SLO dashboards; alerting).
8. **K8s productionization** (HPAs, PDBs, blue/green, secrets store).
9. **Testing** (IB sim suite, chaos, performance, security scans in CI).

---

## 17) Milestones, Deliverables & Acceptance Criteria

### M1 – Foundations (2 weeks)

**Deliverables:** Auth (JWT/refresh, API keys), tenant middleware, RBAC scopes, rate limit middleware, IP allowlists; OpenAPI v1.
**Acceptance:** Login/refresh works; API keys scoped; 95p latency non‑broker <150ms in staging.

### M2 – IB Connector & Health (2–3 weeks)

**Deliverables:** `ibsdk` wrapper, mapper, reconnect logic, health/readiness probes, simulator.
**Acceptance:** Paper account connect/disconnect/reconnect; open orders/executions fetch; SLOs for reconnect p95 <60s.

### M3 – OMS Core (3–4 weeks)

**Deliverables:** Order create/modify/cancel, idempotency store, state machine, executions ingestion, reconciliation worker, audit logs.
**Acceptance:** End‑to‑end paper trade flows incl. partial fills; deterministic idempotency; full audit trail.

### M4 – Market Data (2 weeks)

**Deliverables:** Subscriptions, Redis fan‑out, SSE stream, periodic snapshots, last‑price API, retention.
**Acceptance:** p95 tick fan‑out <100ms; snapshot tables partitioned; backpressure handled.

### M5 – Risk & Compliance (2 weeks)

**Deliverables:** Rule engine, limits CRUD, pre‑trade enforcement, kill switch, circuit breakers, calendars.
**Acceptance:** Simulated breaches stop orders; overrides audited; dashboards show risk status.

### M6 – Eventing & Webhooks (1–2 weeks)

**Deliverables:** Outbound webhooks with HMAC, retries & DLQ, deliveries UI.
**Acceptance:** At‑least‑once delivery with replay protection; signed payloads validate.

### M7 – Observability & Ops (1–2 weeks)

**Deliverables:** Prometheus metrics, tracing, Sentry, Grafana dashboards, alerting policies, runbooks.
**Acceptance:** On‑call drill passes; synthetic trade alerts on failure.

### M8 – Productionization (2 weeks)

**Deliverables:** K8s manifests (HPA, PDB, NetworkPolicies), Vault integration, blue/green deploys, DR/PITR runbook.
**Acceptance:** Blue/green canary successful; PITR verified; disaster drill within RTO/RPO.

---

## 18) Acceptance Test Matrix (sampling)

* **Idempotent POST /orders**: same payload + key returns identical response.
* **Kill switch**: prevents new orders, cancels working orders; audited.
* **Broker reconnect**: orders/executions/positions reconciled; no duplicate fills.
* **Risk throttle**: exceed QPS → 429 + `Retry‑After`; logs metric increment.
* **SSE stream**: client receives ticks within budget under load (10k ticks/s fan‑out).

---

## 19) Operational Runbooks (abridged)

* **Rotate IB creds:** Pause strategies → rotate in Vault → restart connector → verify paper → resume.
* **Schema migration:** Apply additive migrations during blue; switch traffic; apply cleanup; monitor p95.
* **Hotfix rollback:** Roll back image; invalidate idempotency cache if schema drift; reconcile orders.

---

## 20) Appendices

### A) RBAC Scopes (normalized)

```
auth:login, tenants:admin, tenants:manage,
brokers:connect, brokers:view,
orders:place, orders:cancel, orders:modify, orders:view,
positions:view, pnl:view,
strategies:manage, strategies:run, strategies:view,
risk:override, risk:manage, marketdata:subscribe,
webhooks:manage, system:admin
```

### B) Key Index Plan (examples)

* `order (tenant_id, created_at desc)`; `order (tenant_id, client_order_id)` unique; `execution (order_id, executed_at)`; `tick_data (instrument_id, tick_time)` partition key.

### C) API Error Codes (subset)

* `RISK_LIMIT_BREACH`, `COMPLIANCE_BLOCKED`, `BROKER_REJECT`, `IDEMPOTENT_REPLAY`, `RATE_LIMITED`, `STATE_CONFLICT`, `VALIDATION_ERROR`.

---

## 21) Conclusion

This blueprint delivers a cohesive, enterprise‑grade OMS centered on IB with clear operational rigor. It unifies prior artifacts, formalizes missing pieces, and sequences the work with concrete acceptance criteria. Executing milestones M1–M8 brings the platform to production quality with a durable foundation for future multi‑broker expansion, advanced risk, and analytics.
