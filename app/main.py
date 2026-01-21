import time
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.telemetry import JsonlLogger

app = FastAPI(title="Mini Observability API")
logger = JsonlLogger(filepath="logs/logs.jsonl")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid4())
    start = time.perf_counter()

    status_code = 500
    error_message = None

    try:
        response: Response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as e:
        error_message = f"{type(e).__name__}: {e}"
        return JSONResponse(status_code=500, content={"error": "unhandled_exception"})
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        event = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query),
            "status_code": status_code,
            "latency_ms": round(elapsed_ms, 2),
        }
        if error_message:
            event["error"] = error_message
        logger.log(event)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/work")
def work(ms: int = 50):
    time.sleep(ms / 1000.0)
    return {"ok": True, "slept_ms": ms}


@app.get("/error")
def error():
    return JSONResponse(status_code=500, content={"error": "forced"})
