import json
from collections import Counter
from pathlib import Path

LOG_PATH = Path("logs/logs.jsonl")


def percentile(values, p):
    k = int((len(values) - 1) * p / 100)
    return values[k]


def main():
    latencies = []
    status_counts = Counter()

    with LOG_PATH.open() as f:
        for line in f:
            event = json.loads(line)
            latencies.append(event["latency_ms"])
            status_counts[event["status_code"]] += 1
    sorted_latencies = sorted(latencies)

    print("Total requests:", len(latencies))
    print("Status counts:", dict(status_counts))
    print("p50 latency:", percentile(sorted_latencies, 50))
    print("p95 latency:", percentile(sorted_latencies, 95))
    print("p99 latency:", percentile(sorted_latencies, 99))


if __name__ == "__main__":
    main()
