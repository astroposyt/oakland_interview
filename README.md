# Stock Price Monitor

A flexible, scalable stock price monitoring system demonstrating data ingestion, storage, and real-time visualisation. Built to showcase my approach to architectural thinking, trade-offs, and iteration on a realistic data engineering problem.

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Architecture](#architecture)
4. [Design Decisions & Trade-offs](#design-decisions--trade-offs)
5. [What Works Well](#what-works-well)
6. [Known Limitations & Future Improvements](#known-limitations--future-improvements)
7. [Deployment](#deployment)

---

## Overview

### Live Demo

Experience the system in action at: **http://167.233.99.14:8000/control-panel**

#### Demo Strategy

When exploring the system, I recommend **opening two browser tabs side-by-side:**

1. **Control Panel Tab** – http://localhost:8000/control-panel or deployed URL
   - Add a new stock ticker
   - Click "Trigger Sync" to fetch data

2. **Pipeline Deck Tab** – http://localhost:8000/pipeline-deck  
   - Watch the pipeline visualisation update in **real-time** as data flows through Bronze → Silver → Gold layers
   - This shows the medallion architecture in action

The pipeline deck is the killer feature: you see data mutations propagate through the system instantaneously.

### Video Walkthroughs

- **[System Overview & Architecture](https://www.loom.com/share/193cf02a8f2946e58da171223fd556fc)** – Conceptual walk-through of the design and data flow (watch at 1.5x–2x speed)
- **[Live Demo](https://www.loom.com/share/6b3ff9a411764ff89aa178f0d774cfdb)** – Adding stocks, triggering syncs, and watching real-time updates in the pipeline deck

---

## Getting Started

### Prerequisites

- Docker Engine (with Docker Compose 3.8+)
- Make (recommended)
- Git

### Local Setup

#### Step 1: Clone and Configure

```bash
git clone https://github.com/astroposyt/oakland_interview.git
cd stock-price-monitor
cp .env.example .env
```

By default, `USE_MOCK_API=true` lets you run the entire system locally without external API calls. Mock data is provided for Apple (AAPL) and IBM (IBM).

#### Step 2: Start the System

```bash
make start
```

On Windows:
```powershell
docker-compose up -d
```

This starts:
- PostgreSQL database
- FastAPI backend server
- Dozzle log viewer

#### Step 3: Initialise the Database

```bash
make init-db
```

On Windows:
```powershell
docker-compose exec postgres psql -U postgres -f /docker-entrypoint-initdb.d/init.sql
```

#### Step 4: Access the Platform

| Interface | URL | Purpose |
|-----------|-----|---------|
| **Control Panel** | http://localhost:8000/control-panel | Manage stocks and trigger syncs |
| **Data Viewer** | http://localhost:8000/data-viewer | Inspect data layers |
| **Pipeline Deck** | http://localhost:8000/pipeline-deck | Visual ETL pipeline |
| **API Documentation** | http://localhost:8000/docs | Swagger UI |
| **Logs** | http://localhost:8080 | Dozzle log aggregation |

### CLI Commands

```bash
# Add a stock
make cli-add t=GOOG n="Alphabet Inc."

# Trigger the pipeline
make cli-sync

# Remove a stock
make cli-untrack t=GOOG

# View latest prices from Gold layer
make cli-gold-prices

# Run tests
make test

# Stop containers (preserves data)
make stop

# Full reset (destroys all data and containers)
make clean

# Restart containers without losing data
make restart
```

### Database Reset & Data Management

To start fresh with a clean database:

```bash
# Option 1: Full reset (nuclear option)
make clean
make start
make init-db

# Option 2: Reset only the database (keep containers running)
docker-compose down -v
docker-compose up -d
make init-db

# Option 3: Clear data while keeping schema (via CLI)
make cli-sync  # Fetches fresh data from API
```

On Windows:
```powershell
# Full reset
docker-compose down -v
docker-compose up -d
docker-compose exec postgres psql -U postgres -f /docker-entrypoint-initdb.d/init.sql
```

### Using the Live API

To connect to real stock data from Alpha Vantage:

1. Get a free API key: https://www.alphavantage.co/api/
2. Update `.env`:
   ```
   USE_MOCK_API=false
   VANTAGE_API_KEY=your_key_here
   ```
3. Restart: `make restart`

---

## Architecture

### System Design

![Architecture Diagram](https://raw.githubusercontent.com/astroposyt/oakland_interview/main/imagesForReadMe/architectureNow.png)

**Core Components:**
- **Backend:** FastAPI (async Python)
- **Database:** PostgreSQL with medallion architecture
- **Data Provider:** Vantage Alpha API (or local mock)
- **Infrastructure:** Docker Compose
- **CI/CD:** GitHub Actions

### Data Flow: Medallion Architecture

The system uses a three-layer approach optimised for read-heavy workloads:

```
┌──────────────────────────────────────────────────────┐
│                 GOLD LAYER                           │
│          (Materialised Views – Latest Data)          │
│                                                      │
│  • daily_stock_prices_latest (denormalised view)     │
│  • Optimised for O(1) dashboard queries              │
└──────────────────────────────────────────────────────┘
                          ▲
                          │
┌─────────────────────────┼──────────────────────────┐
│          SILVER LAYER   │                          │
│   (Normalised Metadata & Aggregates)               │
│                                                    │
│  • stock_metadata (company info, active flag)      │
│  • price_history (normalised daily prices)         │
│  • stock (scheduling metadata)                     │
└────────────────────────────────────────────────────┘
                          ▲
                          │
┌─────────────────────────┼──────────────────────────┐
│          BRONZE LAYER   │                          │
│      (Raw API Responses)                           │
│                                                    │
│  • raw_api_responses (unmodified JSON)             │
│  • Enables data retrofitting without re-API calls  │
│  • Immutable audit trail                           │
└────────────────────────────────────────────────────┘
```

**Design Rationale:**
- **Bronze:** Preserves raw responses for debugging and retrofitting without hitting API rate limits
- **Silver:** Normalised operational data with strong schemas
- **Gold:** Pre-aggregated latest data for instant dashboard performance

### API Integration Strategy

```
Local Mock API ──┬──→ Lightweight development (no rate limits)
                 │
                 └──→ Switch to live API when needed
                      ↓
                 Vantage Alpha API
                      ↓
                 Anti-Corruption Layer (Pydantic Validation)
                      ↓
                 Database (UPSERT for idempotency)
```

**Key Decisions:**
- Direct REST calls (no SDK lock-in)
- Strict Pydantic validation as an Anti-Corruption Layer prevents upstream API evolution from corrupting downstream data
- UPSERT strategy ensures idempotency—retries don't create duplicate records

---

## Design Decisions & Trade-offs

This is a working system, not a perfect one. The design reflects specific assumptions and trade-offs made at inception.

### Assumption: Read-Heavy Workload

**Assumption:** Stock data is fetched infrequently (once daily) but read constantly (dashboard queries, WebSocket feeds).

**Decision:** Materialised views in the Gold layer pre-aggregate latest prices for O(1) reads.

**Trade-off:** One-time write cost is higher (3 tables to manage), but every subsequent read is instant.

### Assumption: Distributed System Scaling

**Current State:** Internal cron scheduler works fine for a single instance.

**Problem:** Scaling to multiple replicas requires external coordination to avoid duplicate API calls and conflicting writes.

**Decision:** Kept scheduler internal for simplicity given current scale.

**Trade-off:** Easy to understand today; would need refactoring to external orchestrator (Airflow, Dagster) when horizontal scaling is required.

---

## What Works Well

### 1. Reliable Data Quality via Anti-Corruption Layer (ACL)

**Implementation:**
- Pydantic models enforce strict type contracts at the entry point
- JSON schema validation catches malformed responses
- Database constraints prevent invalid states downstream
- All validation happens upstream, near the data source

**Why This Matters:**
External APIs evolve, fail, or send unexpected data. By implementing a strict anti-corruption layer, invalid data never corrupts the Silver or Gold layers. This is a domain-driven design pattern that pays dividends as the system scales.

**Result:**
- Silent data corruption is impossible
- Validation failures are loud and traceable
- Safe schema evolution without legacy baggage
- Audit trail of rejected data for debugging

### 2. Portable, Cloud-Agnostic Deployment

**Implementation:**
- Complete containerisation via Docker
- Identical stack on laptop, staging, production
- Makefile for human-friendly commands
- GitHub Actions CI/CD with automated testing
- Environment configuration via `.env`

**Why This Matters:**
New team members onboard in minutes. No "works on my machine" surprises. Staging and production are provably identical.

**Result:**
- Reproducible deployments across any platform (AWS, GCP, Azure, Kubernetes)
- Full stack testing before merge
- Easy cloud provider migration

### 3. Fast Development via Mock Data

**Implementation:**
- Local mock server returns realistic API responses
- Toggle between mock and live API via one environment variable
- Avoids API rate limits during iteration

**Why This Matters:**
Hitting a local server (< 1ms) beats rate-limited external APIs (1-2s+).

**Result:**
- I iterate 10x faster during feature work
- Tests don't flake due to network timeouts
- I can craft edge-case scenarios manually

### 4. Automated CI/CD Testing Infrastructure

**Implementation:**
- GitHub Actions runs full test suite on every push
- Unit tests run in milliseconds (no database dependencies)
- Integration tests validate end-to-end data pipelines
- Docker image builds automatically on merge
- Automated deployment gates before production

**Why This Matters:**
Testing before deployment catches bugs early. Automation removes manual error and accelerates iteration—I can ship with confidence that code has been validated before reaching production.

**Result:**
- No broken code reaches production
- Developers get fast feedback (tests run in ~2 minutes)
- Deployment is one-click once tests pass
- New features are safer to ship

### 5. Modular, Testable Architecture

**Implementation:**
- Domain-Driven Design separates concerns (routing, business logic, data access)
- Dependency injection for external clients
- Each component has a single responsibility

**Why This Matters:**
Unit tests run in milliseconds without touching the database. Swapping API providers or databases requires minimal code changes.

**Result:**
- Code is easy to reason about and modify
- Tests give fast feedback
- New features don't require refactoring existing code

### 6. Idempotent Data Operations

**Implementation:**
- UPSERT strategy on all writes
- No side effects from retries
- Deduplication at the database layer

**Why This Matters:**
Network failures happen. When they do, retrying shouldn't create duplicate records or inconsistent states.

**Result:**
- Safe to retry failed API calls
- Scheduled tasks can be triggered without risk
- Data remains consistent under failures

---

## Known Limitations & Future Improvements

### 1. Raw JSON in PostgreSQL (Bronze Layer)

**Current State:**
Raw API responses stored in database as JSON blobs.

**Why It's a Problem:**
- PostgreSQL is expensive for historical data storage
- Mixing OLTP (operational) and OLAP (analytical) workloads
- Scales poorly as data volume grows

**Why I Did It:**
- Simplicity: no external dependencies during setup
- Rapid iteration: database-only solution
- Good enough for interview scope

**Future Approach:**
- Migrate to cloud object storage (AWS S3, Google Cloud Storage)
- Compress with Parquet format for efficient querying
- Archive old data to cheaper storage tiers
- Cost savings multiply at scale

### 2. Internal Scheduler (No External Orchestration)

**Current State:**
Basic cron-like scheduler within the API process.

**Why It's a Problem:**
- Single point of failure; no redundancy
- No retry logic for failed API calls
- No task history or audit trail
- Doesn't scale to distributed systems

**Why I Did It:**
- Works fine for one instance
- No operational overhead
- Easier to reason about during development

**Future Approach:**
- Apache Airflow or Dagster for external orchestration
- Automatic retries with exponential backoff
- Multi-machine scheduling for parallel tasks
- Task history and SLA monitoring

### 3. Materialised View Refresh Strategy

**Current State:**
Gold layer refresh recalculates across all historical data.

**Why It's a Problem:**
- Refresh time grows linearly with data volume
- Becomes expensive after 6-12 months of data

**Why I Did It:**
- Simple implementation
- Sufficient for current data volumes

**Future Approach:**
- Incremental refresh: only compute new/changed records
- Partition by date
- Background refresh jobs with query caching
- Event-driven updates on data mutation

### 4. WebSocket Implementation

**Current State:**
WebSocket sends all data every 1.5 seconds regardless of changes.

**Why It's a Problem:**
- Clients receive thousands of redundant messages
- No real advantage over HTTP polling
- High CPU and bandwidth cost

**Why I Did It:**
- Simple to implement
- "Nice to have" feature for demo

**Future Approach:**
- Listen for database mutations
- Send deltas only when data changes
- Reduces client message throughput by 10x

### 5. Validation Business Logic

**Current State:**
Basic validation; assumes happy-path scenarios.

**Why It's a Problem:**
- Likely edge cases not yet discovered
- Real-world data is messier than expected

**Why I Did It:**
- Focus on architecture over edge cases
- Validation logic emerges from real usage

**Future Approach:**
- Collect validation failures in Dead Letter Queue
- Iteratively add test cases as edge cases appear
- Involve domain experts to refine rules

### 6. Schema Migrations

**Current State:**
Static `init.sql` file; schema changes are manual.

**Why It's a Problem:**
- No version control of schema changes
- Manual updates are error-prone
- No rollback capability
- Prevents zero-downtime deployments

**Why I Did It:**
- Schema rarely changes during initial development
- Flyway/Alembic add operational complexity

**Future Approach:**
- Alembic (Python) or Flyway for versioned migrations
- Track all schema changes in version control
- Enable zero-downtime deployments

### 7. Authentication & Security

**Current State:**
No authentication; assumes trusted network.

**Why It's a Problem:**
- API routes are open to anyone
- No audit trail of actions
- Not suitable for production or regulated environments

**Why I Did It:**
- Interview brief didn't specify security requirements
- Focus on data engineering, not security
- Authentication strategy depends on customer regulations

**Future Approach (when requirements are clear):**
- JWT-based authentication for API routes
- Role-based access control (admin, read-only)
- Password hashing with Argon2
- API keys in secrets manager (not `.env`)
- TLS 1.3 for all communication
- Audit logging for sensitive operations

### 8. Observability & Monitoring

**Current State:**
Docker logs aggregated via Dozzle.

**Why It's a Problem:**
- Dozzle is development-focused; not suitable for production
- No metrics, alerts, or SLA monitoring
- Hard to diagnose issues in distributed systems

**Future Approach:**
- Grafana Loki + Promtail for centralised logging
- Prometheus + Grafana for metrics and dashboards
- Alerting on error rates and latency
- Real-time issue detection

---

## Deployment

### GitHub Actions CI/CD

The project includes automated testing and deployment:

```
Git Push → Unit Tests → Integration Tests → Docker Build → Deploy
```

**Current Status:**
- Automatic testing before deployment
- Reduces human error
- Docker-based deployment ensures consistency

**Future Enhancements:**
- More granular testing stages
- Manual approval gates before production
- Automated rollback on failure
- Staging environment validation

### Local Deployment

See [Getting Started](#getting-started) for Docker Compose setup.

### Cloud Deployment

The system is currently deployed at **http://167.233.99.14:8000/control-panel**

**Note:** CLI commands are not available on the deployed version due to security constraints.

---

## Summary: Key Commands

| Task | Command |
|------|---------|
| **First-time setup** | `make start && make init-db` |
| **Add a stock** | `make cli-add t=TICKER n="Company Name"` |
| **Trigger data sync** | `make cli-sync` |
| **Open control panel** | http://localhost:8000/control-panel |
| **Check logs** | http://localhost:8080 |
| **Run tests** | `make test` |
| **Stop all containers** | `make stop` |
| **Full reset** | `make clean && make start && make init-db` |

---

## Approach & Thinking

This project prioritises **clarity of design thinking** over feature completeness. Every major decision—from the medallion architecture to the mock API—reflects a deliberate trade-off.

**What I'd highlight for review:**
1. **Data reliability:** Upstream validation prevents corruption of downstream layers
2. **Operational simplicity:** Medallion architecture keeps developer experience clean while supporting future scaling
3. **Honest assessment:** I've documented what works well and what needs rework, with clear rationale for each
4. **Rapid iteration:** Mock API and Docker setup let new contributors start immediately

**If you have questions or spot issues, that's the point—this is a foundation for discussion, not a finished product.**

---

## Getting Help

- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Live Logs:** http://localhost:8080 (Dozzle)
- **Architecture Questions:** See [Architecture](#architecture) and [Design Decisions](#design-decisions--trade-offs)