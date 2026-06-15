# Stock Price Monitor

> A flexible, scalable stock price monitoring system with real-time data ingestion, storage, and visualization.

## Table of Contents

1. [Demo](#demo)
2. [Getting Started](#getting-started)
3. [CI/CD Pipeline](#cicd-pipeline)
4. [Architecture Overview](#architecture-overview)
5. [Strengths](#strengths--weaknesses-analysis)
6. [Future Improvements](#future-improvements)

---

## Demo

https://www.loom.com/share/6b3ff9a411764ff89aa178f0d774cfdb

## Slide video (maybe watch at 2x speed)

https://www.loom.com/share/193cf02a8f2946e58da171223fd556fc

### Accessing the Deployed Instance

Experience the live system in action:

1. **Open Control Panel** (First Tab)  
   URL: http://167.233.99.14:8000/control-panel

2. **Open Pipeline Deck** (Second Tab)  
   URL: http://167.233.99.14:8000/pipeline-deck

3. **Navigate the Pipeline Visualisation**  
   Click through the slides on the pipeline-deck to understand data flow

4. **Add a Stock**  
   In the control-panel, enter a ticker symbol and company name

5. **Trigger Data Sync**  
   Click the sync button to fetch and process data

6. **Watch Real-Time Updates**  
   The pipeline-deck updates near-instantaneously with new data

**Note:** CLI access is not available on the deployed version due to security constraints.

---

## Getting Started

### Prerequisites

- **Docker Engine** (with Docker Compose 3.8+)
- **Make** (optional but recommended)
- **Git** (for cloning the repository)

### Initial Setup

#### Step 1: Clone the Repository

```bash
git clone https://github.com/astroposyt/oakland_interview.git
cd stock-price-monitor
```

#### Step 2: Configure Environment Variables

Copy the example environment file to create your local configuration:

```bash
cp .env.example .env
```

The default configuration uses the mock API (`USE_MOCK_API=true`), which allows you to run the entire pipeline locally without needing an API key. Mock data is provided for Apple (AAPL) and IBM (IBM). When using the mock, data falls back to the IBM if a different ticker is used

#### Step 3: Start the Stack

```bash
make start
```
or on windows

```powershell
docker-compose up -d
```

This command:
1. Builds Docker images (if necessary)
2. Starts PostgreSQL
3. Launches the FastAPI backend server
4. Initialises Dozzle log viewer

#### Step 4: Initialise the Database (First Run Only)
On first run, the database needs initialised with `init.sql`.

```bash
make init-db
```
or on windows

```powershell
docker-compose exec postgres psql -U postgres -f /docker-entrypoint-initdb.d/init.sql
```
This creates all tables in the database.

### Using the Live API

To use the live Vantage Alpha API instead of mock data:

1. Obtain a free API key from [Alpha Vantage](https://www.alphavantage.co/api/)
2. Update `.env`:
   ```bash
   USE_MOCK_API=false
   VANTAGE_API_KEY=your_actual_key_here
   ```

3. Restart the stack: `make restart`

### Accessing the Platform

Once running, access the platform at:

| Interface | URL | Purpose |
|-----------|-----|---------|
| **Control Panel** | http://localhost:8000/control-panel | Manage stocks and trigger syncs |
| **Data Viewer** | http://localhost:8000/data-viewer | Inspect Bronze, Silver, Gold layers |
| **Pipeline Deck** | http://localhost:8000/pipeline-deck | Visual ETL pipeline diagram |
| **Dozzle Logs** | http://localhost:8080 | Real-time container logs |

### Stopping and Cleaning Up

```bash
# Stop containers (preserves database)
make stop

# Reset everything (destroys database)
make clean
```
or on windows

```powershell
docker-compose exec api-server pytest
```

```powershell
docker-compose down -v
```
---

## CLI Operations

Interact with the system programmatically without the web interface:

### Add a Stock

```bash
make cli-add t=<TICKER> n="<COMPANY_NAME>"
```

**Example:**
```bash
make cli-add t=GOOG n="Alphabet Inc."
```

### Trigger Full Data Pipeline

```bash
make cli-sync
```

Fetches data for all tracked stocks, validates, and loads into the database.

### Remove a Stock

```bash
make cli-untrack t=<TICKER>
```

**Example:**
```bash
make cli-untrack t=GOOG
```

### View Latest Prices

```bash
make cli-gold-prices
```

Displays recent price data from the Gold materialised views.

---

## Makefile Command Reference

| Command | Purpose |
|---------|---------|
| `make start` | Build and start all containers |
| `make stop` | Stop containers (preserves data) |
| `make restart` | Restart API server only |
| `make clean` | Destroy all containers and volumes |
| `make logs` | Tail live logs from all services |
| `make test` | Run full Pytest suite |
| `make test-unit` | Run unit tests only |
| `make test-integration` | Run integration tests only |
| `make coverage` | Generate test coverage report |

---

## CI/CD Pipeline

GitHub Actions automates testing and deployment whenever you push code.

**Workflow:**
```
Git Push → Code Tests → Docker Build → Publish → Deploy
```

**Features:**
- Automatic testing before deployment
- Reduces human error during releases
- Accelerates development cycles
- Docker-based deployment for consistency

**Future Enhancements:**
- More granular testing stages
- Manual verification gates
- Automated rollback mechanisms
- Staging environment validation

---

## Architecture Overview

### Introduction

This project implements a stock price monitoring system with a flexible, scalable architecture designed to handle real-time data ingestion, storage, and visualisation. The design prioritises flexibility and extensibility whilst maintaining clean separation of concerns.

### System Architecture



### Technology Stack & Rationale

#### Backend: FastAPI

**Why FastAPI?**
- Native async/concurrent I/O operations, nearly matching Go performance
- Massive ecosystem for ML, data processing, and integrations
- Excellent REST API and WebSocket support
- Learning opportunity for new frameworks

#### Database: PostgreSQL

**Why PostgreSQL?**
- Standard SQL ensures consistency and portability
- Excellent for structured, API-sourced data
- Extensible with TimescaleDB for future time-series optimisation
- Normalised schema design with medallion architecture

**Future Enhancement:** TimescaleDB extension for handling large volumes of time-series data.

#### Data Provider: Vantage Alpha API

**Why Vantage Alpha?**
- Free tier available
- Traditional REST API (no SDK lock-in)
- Multiple data points available
- Easy provider switching in future

#### Infrastructure: Docker & Docker Compose

**Why containerisation?**
- Portability across environments
- Reproducible deployments
- Easy scaling and orchestration
- Makefile wrappers for simplified commands

#### CI/CD: GitHub Actions

**Why GitHub Actions?**
- Native repository integration
- Enforced testing before deployment
- Automated, reliable deployment pipeline

### Database Schema: Medallion Architecture

The database follows a three-layer medallion approach optimised for read-heavy workloads:

```
┌──────────────────────────────────────────────────────┐
│                 GOLD LAYER                           │
│          (Materialised Views - Latest Data)          │
│                                                      │
│  ◆ daily_stock_prices_latest (denormalised view)    │
│  ◆ Accelerates frequent read queries                │
└──────────────────────────────────────────────────────┘
                          ▲
                          │
┌──────────────────────────┼──────────────────────────┐
│          SILVER LAYER    │                          │
│   (Normalised Metadata & Aggregates)               │
│                                                    │
│  • stock_metadata (company info, active flag)     │
│  • price_history (normalised daily prices)        │
│  • stock (with should_fetch flag for scheduling) │
└──────────────────────────────────────────────────────┘
                          ▲
                          │
┌──────────────────────────┼──────────────────────────┐
│          BRONZE LAYER    │                          │
│      (Raw API Responses)                           │
│                                                    │
│  ◆ raw_api_responses (raw JSON storage)          │
│  ◆ Enables retroactive data fixes without re-API  │
│  ◆ Audit trail & historical accuracy              │
└──────────────────────────────────────────────────────┘
```

**Design Rationale:**
- **Bronze Layer:** Raw JSON responses preserved for retrofitting and debugging
- **Silver Layer:** Normalised data with metadata for operational queries
- **Gold Layer:** Materialised view of latest data accelerates monitoring queries

### API Integration

**Approach:** Direct REST (No SDK)

```
┌──────────────────┐
│  Local Mock      │  ← Avoid rate limits during development
│  Data Server     │     Deterministic data for testing
└──────────────────┘
         │
         ├─→ Toggle to live API when ready
         │
┌────────▼─────────────────┐
│  Vantage Alpha API       │
│  (Live Stock Data)       │
└──────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  JSON Validation         │
│  Data Validation         │
│  Defensive Coding        │  ← Prevents downstream issues
└──────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Database Insertion      │
│  (UPSERT Strategy)       │  ← Ensures idempotency
└──────────────────────────┘
```

**Key Features:**
- Defensive validation at each layer (JSON schema, data types, constraints)
- Idempotent operations using UPSERT (INSERT ... ON CONFLICT DO UPDATE)
- Connection pooling and batch inserts for efficiency

### Scheduling & Orchestration

**Current Implementation:**
- Internal cron scheduler with basic coordination
- Single daily API call per configured stock at 1:00 AM UTC
- Dead man's switch function in place

**Future Improvement:**
- External orchestrator (Apache Airflow, Kubernetes CronJob)
- Better retry logic and exponential backoff
- Task history and audit trail

### Frontend Architecture

**Approach:** Static HTML + Tailwind CSS

**Design Philosophy:** Keep frontend simple and static to maintain clean backend separation.

**Technology:**
- Static HTML with vanilla JavaScript
- Tailwind CSS for styling
- WebSocket connections for real-time updates
- REST API calls for data operations

**Future Frontend:** React or Svelte
- Only if full interactive requirements emerge
- Svelte preferred for lightweight package size

### Communication Protocols

**REST API:**
- Standard HTTP endpoints for data queries
- Stateless request/response pattern
- Used for initial data loads and updates

**WebSocket:**
- Real-time bidirectional communication
- Used for live stock price monitoring
- Basic implementation with room for optimisation

**Future Enhancement:** Event-driven architecture with database change detection

### Logging & Observability

**Current:** Dozzle
- Simple Docker log aggregation
- Development-focused tool

**Future:** Observability Stack
- **Logs:** Grafana Loki + Promtail
- **Metrics:** Prometheus + Grafana dashboards
- **Benefits:** Real-time issue detection, performance trending

### Security Considerations

**Current Status:** No security implemented

**Reasoning:**
- Requirements not fully specified
- To be implemented as needs become clear

**Future Implementation:**
- JWT token-based authentication
- Role-based access control (RBAC)
- Password encryption at rest (Argon2)
- API keys in secrets manager
- TLS 1.3 for in-transit communication
- Audit logging for sensitive operations
- Rate limiting on API endpoints

---

## Strengths & Weaknesses Analysis

### What Works Well (Strengths)

#### 1. Scalable I/O & Performance Architecture

**What:**
- FastAPI with async/await for non-blocking concurrent operations
- Connection pooling to prevent database saturation
- Medallion architecture's Gold layer with materialised views
- Denormalised, pre-aggregated data for O(1) read performance

**Why It Matters:**
The design prioritises read-heavy workloads with minimal writes. Materialised views eliminate expensive joins on every read, enabling instant queries without touching Silver or Bronze layers.

**Impact:**
- Dashboard queries complete in milliseconds
- Handles thousands of concurrent WebSocket connections
- Reduced database CPU overhead

#### 2. Portable & Cloud-Agnostic Deployment

**What:**
- Complete containerisation via Docker
- Multi-service orchestration with `docker-compose.yml`
- Makefile for human-friendly commands
- GitHub Actions CI/CD with automated testing
- Environment-agnostic configuration via `.env`

**Why It Matters:**
The entire stack runs identically on a developer's laptop, staging server, or production cloud infrastructure (AWS, GCP, Azure, Kubernetes).

**Impact:**
- New developers onboard in minutes
- Staging and production environments provably identical
- Easy migration between cloud providers
- Full stack testing in CI/CD before merge

#### 3. Data Reliability & Strict Input Contracts

**What:**
- Pydantic models enforce strict data validation
- JSON schema validation catches malformed responses
- Type hints enable static type checking
- Database constraints prevent invalid states

**Why It Matters:**
Upstream APIs may evolve, send unexpected data types, or introduce bugs. Pydantic acts as an anti-corruption layer: invalid data is rejected before it corrupts the Silver layer.

**Impact:**
- Silent data corruption is impossible
- Validation failures are loud and traceable
- Audit trail of rejected data
- Schema evolution is safe

#### 4. Decoupled, Modular Architecture

**What:**
- Domain-Driven Design principles separate concerns
- Routing layer handles HTTP only
- Business logic layer contains domain rules
- Data access layer isolates database queries
- Dependency Injection pattern for external clients

**Why It Matters:**
Each layer has a single responsibility. Swapping implementations requires changing only the dependency injection container.

**Impact:**
- Unit tests run in milliseconds without DB
- Replacing API providers requires minimal code changes
- New developers quickly understand code flow
- Adding features doesn't require refactoring existing code

#### 5. Development Velocity via Mock Data

**What:**
- Local mock data server returns real responses
- Toggle between mock and live API via configuration
- Scenarios can be manually crafted for edge-case testing
- Avoids API rate limits during development

**Why It Matters:**
Developers iterate faster hitting a local mock server (< 1ms) versus rate-limited external API (1-2s+).
---

### Future Improvements

#### 1. Robust Pipeline Orchestration

**Current Limitation:**
- No retry logic for failed API calls
- No task history or audit trail
- Single node; no redundancy
- No visibility into task state

**Future Approach:**
- Apache Airflow or Dagster for external orchestration
- Automatic retries with exponential backoff
- Multi-machine scheduling for parallel tasks

#### 2. Dedicated Object Storage for Bronze Layer

**Current Limitation:**
- Raw API responses stored in PostgreSQL
- Expensive storage for historical data
- Mixing OLTP and OLAP in one database

**Future Approach:**
- Migrate to cloud object storage (AWS S3, GCS)
- Partition by date for efficient querying
- Archive old data to cheaper storage tiers

#### 3. Database Migration Management

**Current Limitation:**
- Schema initialised via static `init.sql`
- Manual SQL edits for changes
- No version control of schema
- No rollback capability

**Future Approach:**
- Alembic or Flyway for automated migrations
- Version-controlled schema changes
- Zero-downtime deployments
- Audit trail of all changes


#### 4. Dead Letter Queue (DLQ) for Failed Validations

**Current Limitation:**
- Invalid payloads logged then discarded
- No way to inspect or replay failed data
- Manual data reconstruction required

**Future Approach:**
- Dedicated DLQ table for validation failures
- Dashboard for reviewing failed records
- Add cases to testing suite

**Impact:**
- No silent data loss
- Historical data recoverable without re-API calls
- Compliance audit trail


#### 5. Enterprise Observability & Security

**Current Limitation:**
- Logs to stdout; aggregated locally via Dozzle
- No authentication on API routes
- No encryption for API keys
- No audit logging

**Future Approach:**
- Grafana Loki + Promtail for logging
- Prometheus + Grafana for metrics
- JWT token authentication
- RBAC with admin/read-only roles
- Secrets manager for API keys
- TLS 1.3 for all communication

**Impact:**
- Multi-instance deployments become feasible
- Real-time monitoring and alerting
- Compliance-ready (SOC 2, HIPAA, GDPR)

---

#### 6. Websocket logic

**Current Limitation:**
- Has no logic looking for data mutation etc, simply resends every 1.5 seconds
- Minimal advantage as is over polling

**Future Approach:**
- Only resend data on data mutation

---
#### 7. Business logic

**Current Limitation:**
- Business logic has not been developed properly. There are likely many edge cases

**Future Approach:**
- Properly and iteratively develop validations to ensure data is correct at source

## Getting Help

- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Logs:** http://localhost:8080 (Dozzle)

---

## Summary: Quick Commands

| Task | Command |
|------|---------|
| **First-time setup** | `make start` |
| **Add a stock** | `make cli-add t=TICKER n="Name"` |
| **Fetch latest data** | `make cli-sync` |
| **View dashboard** | http://localhost:8000/control-panel |
| **Check logs** | http://localhost:8080 |
| **Run tests** | `make test` |
| **Stop everything** | `make stop` |
| **Full reset** | `make clean && make start` |