# Mini Observability API

This project demonstrates basic observability by logging every request and analyzing performance metrics from logs.


## Activate Environment 
```bash
source .venv/bin/activate
```
## Run
```bash
uvicorn app.main:app --reload
python3 scripts/generate_traffic.py
python3 scripts/analyze_logs.py
```

## Should run with multiple workers now, try:
```bash
uvicorn main:app --workers 4
```