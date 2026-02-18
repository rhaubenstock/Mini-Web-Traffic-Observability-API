# Mini Observability API

This project demonstrates a basic logging and analysis of basic financial transactions including invoices, payments, and refunds.
Currently write logs to separate files for each process in order to support running with multiple workloads.

## Create Environment
```bash
python3 -m venv .venv
```

## Activate Environment 
```bash
source .venv/bin/activate
```

## Run
```bash
uvicorn app.main:app --reload
python3 scripts/generate_traffic.py
```

## Can be run with multiple workers for higher workloads:
```bash
uvicorn main:app --workers 4
```

## Next Steps
* Containerization
* Data Visualization
* Load Testing
* Log Reconciliation
* API Documentation
