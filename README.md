# Mini Observability API

This project demonstrates basic observability by logging every request and analyzing performance metrics from logs.

## Run
```bash
uvicorn app.main:app --reload
python scripts/generate_traffic.py
python scripts/analyze_logs.py
```