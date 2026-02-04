import time
from uuid import uuid4
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse

from app.telemetry import JsonlLogger

app = FastAPI(title="Mini Observability API")
logger = JsonlLogger(filepath="logs/logs.jsonl")

# --- In-memory "database" (kept intentionally simple) ---
INVOICES: Dict[str, Dict[str, Any]] = {}   # invoice_id -> invoice record
PAYMENTS: Dict[str, Dict[str, Any]] = {}   # payment_id -> payment record
IDEMPOTENCY: Dict[str, str] = {}  # idempotency_key -> payment_id

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_business_event(event: Dict[str, Any]) -> None:
    """
    Writes a second JSONL line representing a business/audit event.
    """
    event.setdefault("timestamp", utc_now_iso())
    event.setdefault("service", "mini-observability-api")
    event.setdefault("schema_version", 1)
    logger.log(event)


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
            "event_type": "http_request",
            "schema_version": 1,
            "service": "mini-observability-api",
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


# --- Accounting-flavored endpoints --- #

@app.post("/invoices")
async def create_invoice(payload: Dict[str, Any]):
    """
    Create an invoice.
    Expected JSON body:
      {
        "customer_id": "CUST-001",
        "amount_cents": 12500,
        "due_days": 30
      }
    """
    customer_id = str(payload.get("customer_id", "")).strip()
    amount_cents = payload.get("amount_cents")
    due_days = payload.get("due_days", 30)

    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required")
    if not isinstance(amount_cents, int) or amount_cents <= 0:
        raise HTTPException(status_code=400, detail="amount_cents must be a positive integer")
    if not isinstance(due_days, int) or due_days <= 0:
        raise HTTPException(status_code=400, detail="due_days must be a positive integer")

    invoice_id = f"inv_{uuid4().hex[:10]}"
    invoice = {
        "invoice_id": invoice_id,
        "customer_id": customer_id,
        "amount_cents": amount_cents,
        "due_days": due_days,
        "created_at": utc_now_iso(),
        "paid_cents": 0,
        "status": "open",
    }
    INVOICES[invoice_id] = invoice

    log_business_event({
        "event_type": "invoice_created",
        "invoice_id": invoice_id,
        "customer_id": customer_id,
        "amount_cents": amount_cents,
        "currency": "USD",
        "due_days": due_days,
    })

    return {"invoice_id": invoice_id, "status": "created"}


@app.post("/payments")
async def create_payment(payload: Dict[str, Any]):
    """
    Record a payment against an invoice.
    Expected JSON body:
      {
        "invoice_id": "inv_2c9a5f5855",
        "amount_cents": 5000,
        "method": "ach",
        "idempotency_key": "inv_2c9a5f5855--ach--5000"
      }
    """

    invoice_id = str(payload.get("invoice_id", "")).strip()
    amount_cents = payload.get("amount_cents")
    method = str(payload.get("method", "ach")).strip().lower()
    idempotency_key = payload.get("idempotency_key")

    if idempotency_key:
        idempotency_key = str(idempotency_key).strip()
        if idempotency_key in IDEMPOTENCY:
            existing_payment_id = IDEMPOTENCY[idempotency_key]
            existing = PAYMENTS.get(existing_payment_id)
            log_business_event({
            "event_type": "duplicate_ignored",
            "invoice_id": invoice_id,
            "amount_cents": amount_cents,
            "payment_method": method,
            "itempotency_key": idempotency_key,
            "reason": "duplicate payment",
        })
            return {
                "payment_id": existing_payment_id,
                "status": "duplicate_ignored",
                "invoice_status": INVOICES[existing["invoice_id"]]["status"] if existing else "unknown",
            }


    if not invoice_id:
        raise HTTPException(status_code=400, detail="invoice_id is required")
    if not isinstance(amount_cents, int) or amount_cents <= 0:
        raise HTTPException(status_code=400, detail="amount_cents must be a positive integer")
    if method not in {"ach", "card", "check"}:
        raise HTTPException(status_code=400, detail="method must be one of: ach, card, check")

    inv = INVOICES.get(invoice_id)
    if not inv:
        log_business_event({
            "event_type": "payment_failed",
            "invoice_id": invoice_id,
            "amount_cents": amount_cents,
            "payment_method": method,
            "reason": "invoice_not_found",
        })
        raise HTTPException(status_code=404, detail="invoice not found")

    remaining = inv["amount_cents"] - inv["paid_cents"]
    if amount_cents > remaining:
        log_business_event({
            "event_type": "payment_failed",
            "invoice_id": invoice_id,
            "amount_cents": amount_cents,
            "payment_method": method,
            "reason": "overpayment",
            "remaining_cents": remaining,
        })
        raise HTTPException(status_code=400, detail="payment exceeds remaining balance")

    inv["paid_cents"] += amount_cents
    if inv["paid_cents"] == inv["amount_cents"]:
        inv["status"] = "paid"

    payment_id = f"pay_{uuid4().hex[:10]}"
    payment = {
        "payment_id": payment_id,
        "invoice_id": invoice_id,
        "amount_cents": amount_cents,
        "method": method,
        "created_at": utc_now_iso(),
    }
    PAYMENTS[payment_id] = payment

    if payload.get("idempotency_key"):
        IDEMPOTENCY[str(payload["idempotency_key"]).strip()] = payment_id

    log_business_event({
        "event_type": "payment_received",
        "payment_id": payment_id,
        "invoice_id": invoice_id,
        "amount_cents": amount_cents,
        "currency": "USD",
        "payment_method": method,
        "invoice_status": inv["status"],
    })

    return {"payment_id": payment_id, "status": "recorded", "invoice_status": inv["status"]}


@app.get("/ledger/{invoice_id}")
async def ledger(invoice_id: str):
    """
    Simple ledger view for one invoice.
    """
    inv = INVOICES.get(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="invoice not found")

    payments = [p for p in PAYMENTS.values() if p["invoice_id"] == invoice_id]
    balance = inv["amount_cents"] - inv["paid_cents"]

    return {
        "invoice": inv,
        "payments": payments,
        "outstanding_cents": balance,
    }

@app.post("/refunds")
async def create_refund(payload: Dict[str, Any]):
    invoice_id = str(payload.get("invoice_id", "")).strip()
    refund_cents = payload.get("amount_cents")

    if not invoice_id:
        raise HTTPException(status_code=400, detail="invoice_id is required")
    if not isinstance(refund_cents, int) or refund_cents <= 0:
        raise HTTPException(status_code=400, detail="amount_cents must be a positive integer")

    inv = INVOICES.get(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="invoice not found")

    if refund_cents > inv["paid_cents"]:
        log_business_event({
            "event_type": "refund_failed",
            "invoice_id": invoice_id,
            "amount_cents": refund_cents,
            "reason": "refund_exceeds_paid",
            "paid_cents": inv["paid_cents"],
        })
        raise HTTPException(status_code=400, detail="refund exceeds paid amount")

    refund_id = f"ref_{uuid4().hex[:10]}"
    inv["paid_cents"] -= refund_cents
    if inv["paid_cents"] < inv["amount_cents"]:
        inv["status"] = "open"

    log_business_event({
        "event_type": "refund_issued",
        "refund_id": refund_id,
        "invoice_id": invoice_id,
        "amount_cents": refund_cents,
        "currency": "USD",
        "invoice_status": inv["status"],
    })

    return {"refund_id": refund_id, "status": "issued", "invoice_status": inv["status"]}
