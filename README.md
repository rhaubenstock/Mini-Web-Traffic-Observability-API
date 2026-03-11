# Web Traffic Observability API

**A production-inspired backend service demonstrating modern observability patterns:** structured logging, synthetic load generation, and post-hoc latency/error analysis.

## Overview
This project simulates a production-style backend service for managing invoices and payments, with structured telemetry logging and post-hoc log analysis.

It demonstrates:
- Building a FastAPI service with realistic business workflows
- Structured JSONL logging of latency, HTTP data, and business data per event.
- Synthetic traffic generation
- Log-based latency and error analysis (p50/p95/p99)
- Basic financial reconciliation logic

The goal is to simulate how a real backend service behaves under load and how its telemetry can be analyzed.

## Why This Matters

Most developers only add observability *after* something breaks. This project builds it in from day one.
It shows how to separate **system health** (latency) from **business correctness** (domain events), 
generate realistic load programmatically, and extract insights from logs—without Prometheus or Datadog.

---

## How It Works

The system separates concerns into **three independent components** that mirror production architecture:

### 1. API Service (FastAPI)
The backend exposes REST endpoints for a financial domain (invoices, payments, refunds).
- Every HTTP request is logged with latency and status code via **middleware**
- Domain events (invoice_created, payment_received, payment_failed, refund_issued) are emitted separately
- Business logic validates state consistency (e.g., can't refund more than paid)

**Why:** This separation of *system observability* (HTTP metrics) from *business observability* (domain events) is critical in production. You want to know *what happened* (event count) independently from *how fast* it happened (latency).

### 2. Traffic Generator (Synthetic Load)
Rather than manually curl-ing endpoints, a script generates **realistic, varied load** including:
- Successful invoice creation and payment flows
- Partial payments and overpayments (edge cases)
- Invalid operations (double-payments, missing invoices)
- Natural error conditions

**Why:** This produces meaningful telemetry that reflects how real systems break. Manual testing is slow; synthetic patterns are reproducible.

### 3. Log Analyzer (Post-Hoc Analysis)
Reads all JSONL log files and computes:
- **System health:** Total requests, error rate, p50/p95/p99 latency percentiles
- **Business metrics:** Counts of each domain event type

**Why:** This demonstrates how logs become insights. In production, you'd ship these metrics to Prometheus or Datadog; here, we do it locally to show the principle.

#### Data Flow

[API Service logs events] → [JSONL files on disk] ← [Traffic Generator makes requests] ↓ [Log Analyzer reads logs & computes metrics]

## Quickstart
### 1. Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the API
```
uvicorn app.main:app --reload
```
Open:
http://127.0.0.1:8000/docs


### 3. Generate Traffic
In another terminal:
```
python scripts/generate_traffic.py
```
This simulates invoice creation, payments, and error scenarios.

### 4. Analyze Logs
```
python scripts/analyze_logs.py
```

### Example Output:

```
=== HTTP Metrics ===
Total requests: 312
Errors (>=400): 27
p50 latency: 8.4 ms
p95 latency: 31.2 ms
p99 latency: 65.7 ms

=== Business Events ===
invoice_created: 100
payment_received: 73
payment_failed: 9
refund_issued: 4
```

## Key Design Choices (Why Each Matters)
###  Structured Logging
Logs are written as JSONL (one JSON object per line) to support:
- Easy ingestion into monitoring systems
- Simple offline analysis
- Compatibility with tools like ELK or Datadog

### Separate Business and Latency Reports
- Latency metrics measure system health.
- Business events measure domain correctness.
- This separation mirrors production observability patterns.

### Synthetic Traffic
Rather than manually testing endpoints, a script generates realistic load patterns including:
- Partial payments
- Overpayments
- Invalid operations
This produces meaningful telemetry data.

### Notes
- Logs are written to logs/logs-<pid>.jsonl
- Analyzer reads all matching log files
- File locking uses fcntl (Mac/Linux)

## Future Enhancements
- Export metrics as CSV
- Add time-series latency visualization
- Persist invoices in a database
- Add Prometheus metrics endpoint
