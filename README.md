# Observability-Driven Accounts Receivable API

## Overview
This project simulates a production-style backend service for managing invoices and payments, with structured telemetry logging and post-hoc log analysis.

It demonstrates:
- Building a FastAPI service with realistic business workflows
- Structured JSONL logging of latency, HTTP data, and business data per event.
- Synthetic traffic generation
- Log-based latency and error analysis (p50/p95/p99)
- Basic financial reconciliation logic

The goal is to simulate how a real backend service behaves under load and how its telemetry can be analyzed.

---
## Architecture
The system has three components:
1. **API Service (FastAPI)**
   - Endpoints for invoices, payments, refunds, ledger lookup, and reconciliation
   - Middleware logs every HTTP request with latency and status code
   - Business events (invoice_created, payment_received, etc.) are logged separately
2. **Traffic Generator**
   - Simulates realistic activity (invoice creation as well as partial, invalid, and redundant payments)
   - Generates both successful and failed requests
3. **Log Analyzer**
   - Reads JSONL logs
   - Computes request counts, error counts
   - Calculates p50 / p95 / p99 latency
   - Summarizes business event counts
Logs are written as structured JSON (one event per line).
---
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

## Design Decisions
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
