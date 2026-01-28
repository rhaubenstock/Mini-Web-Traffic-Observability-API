import random
import time
import requests

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"X-Request-Source": "traffic-script"}


def post_json(path: str, payload: dict):
    return requests.post(f"{BASE_URL}{path}", json=payload, headers=HEADERS, timeout=5)


def main():
    random.seed(42)

    # 1) Create invoices
    invoice_ids = []
    for i in range(100):
        customer_id = f"CUST-{random.randint(1, 10):03d}"
        amount_cents = random.choice([2500, 5000, 7500, 10000, 12500, 20000])
        due_days = random.choice([15, 30, 45])

        r = post_json("/invoices", {
            "customer_id": customer_id,
            "amount_cents": amount_cents,
            "due_days": due_days,
        })
        if r.status_code == 200:
            invoice_ids.append(r.json()["invoice_id"])

        time.sleep(random.uniform(0.01, 0.03))

    # 2) Pay some invoices (some full, some partial)
    random.shuffle(invoice_ids)
    to_pay = invoice_ids[:35]

    for inv_id in to_pay:
        # Fetch ledger so we know remaining balance
        ledger = requests.get(f"{BASE_URL}/ledger/{inv_id}", headers=HEADERS, timeout=5)
        if ledger.status_code != 200:
            continue

        inv = ledger.json()["invoice"]
        remaining = inv["amount_cents"] - inv["paid_cents"]

        # 70% chance pay in full, 30% pay partial
        if random.random() < 0.7:
            pay_amount = remaining
        else:
            pay_amount = max(1, remaining // 2)

        method = random.choice(["ach", "card", "check"])

        try:
            idempotency_key =  f"{inv_id}-{method}-{pay_amount}" if random.random() < 0.5 else ""
            post_json("/payments", {
                "invoice_id": inv_id,
                "amount_cents": int(pay_amount),
                "method": method,
                "idempotency_key": idempotency_key,
            })
            #50% chance to resend payment
            post_json("/payments", {
                "invoice_id": inv_id,
                "amount_cents": int(pay_amount),
                "method": method,
                "idempotency_key": idempotency_key,
            })
        except Exception:
            pass

        time.sleep(random.uniform(0.01, 0.03))

    # 3) Generate a few invalid payment attempts (exceptions)
    # 3a) overpayment
    for inv_id in invoice_ids[:3]:
        try:
            post_json("/payments", {
                "invoice_id": inv_id,
                "amount_cents": 999999,  # intentionally too large
                "method": "ach",
            })
        except Exception:
            pass
        time.sleep(random.uniform(0.01, 0.03))

    # 3b) invoice not found
    for _ in range(2):
        fake_invoice = f"inv_{random.randint(1000000000, 9999999999)}"
        try:
            post_json("/payments", {
                "invoice_id": fake_invoice,
                "amount_cents": 5000,
                "method": "card",
            })
        except Exception:
            pass
        time.sleep(random.uniform(0.01, 0.03))


if __name__ == "__main__":
    main()
